/**
 * txt-video 渲染入口
 * 🔒 锁死配置 - 禁止修改
 *
 * 用法: node render.js --text "关键词|主标题|副标题|引用" --speed 1.0
 *
 * 锁死的参数:
 * - 风格: style-1-black (唯一)
 * - backgroundOpacity: 0.6
 * - titleSize: 80
 * - subtitleSize: 42
 * - contentTop: "28%"
 *
 * 唯一授权修改方式: 用户书面确认"同意"
 */

// 加载环境变量
const fs = require('fs');
const path = require('path');
const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf-8');
  envContent.split('\n').forEach(line => {
    const [key, value] = line.split('=');
    if (key && value) {
      process.env[key.trim()] = value.trim();
    }
  });
}

const { generateAudio, getAudioDuration } = require('./api/tts');
const { getBackground } = require('./api/image');
const { execSync } = require('child_process');

// 解析命令行参数
function parseArgs() {
  const args = process.argv.slice(2);
  const params = {};

  args.forEach(arg => {
    const [key, value] = arg.split('=');
    if (key.startsWith('--')) {
      params[key.slice(2)] = value;
    }
  });

  return {
    text: params.text || '',
    speed: parseFloat(params.speed) || 1.0,
    output: params.output || 'out/output.mp4',
    // 🔒 风格已锁死为 style-1-black，忽略任何传入的 style 参数
  };
}

// 解析文案为段落（海报格式）
// 格式：关键词|主标题|副标题|引用，段落间用换行分隔
// 简化格式：主标题（只有一行时使用）
// 长文案自动分段：按句号、问号、感叹号分割，并生成海报格式结构
function parseTextToSegments(text, totalDurationMs) {
  const lines = text.split(/\n/).filter(l => l.trim());

  // 检查是否是海报格式（包含|分隔符）
  const hasPosterFormat = lines.some(line => line.includes('|'));

  // 如果只有一行且没有海报格式，进行智能分段并生成海报结构
  if (lines.length === 1 && !hasPosterFormat) {
    const sentences = text.split(/[。！？\n]/).filter(s => s.trim());
    if (sentences.length > 1) {
      const segmentDuration = totalDurationMs / sentences.length;
      let currentTime = 0;
      return sentences.map((sentence, index) => {
        // 为每个句子生成海报格式结构
        // 第一句作为keyword，整句作为title，后半句作为subtitle
        const words = sentence.trim().split(/[，、；：]/);
        let keyword = '';
        let title = sentence.trim();
        let subtitle = '';
        let quote = '';

        if (words.length >= 3) {
          keyword = words[0].substring(0, 4); // 取前4字作为关键词
          title = words.slice(0, 2).join(''); // 前两部分作为主标题
          subtitle = words.slice(2).join(''); // 后部分作为副标题
        } else if (words.length >= 2) {
          keyword = words[0].substring(0, 4);
          title = words[0];
          subtitle = words[1] || '';
        }

        const segment = {
          keyword: keyword,
          title: title,
          subtitle: subtitle,
          quote: quote,
          startMs: Math.round(currentTime),
          endMs: Math.round(currentTime + segmentDuration),
        };
        currentTime += segmentDuration;
        return segment;
      });
    }
    return [{ title: text, startMs: 0, endMs: totalDurationMs }];
  }

  if (lines.length === 0) {
    return [{ title: text, startMs: 0, endMs: totalDurationMs }];
  }

  const segmentDuration = totalDurationMs / lines.length;
  let currentTime = 0;

  const segments = lines.map((line) => {
    const parts = line.trim().split('|').map(p => p.trim());

    let segment;
    if (parts.length >= 4) {
      // 完整格式：关键词|主标题|副标题|引用
      segment = {
        keyword: parts[0],
        title: parts[1],
        subtitle: parts[2],
        quote: parts[3],
        startMs: Math.round(currentTime),
        endMs: Math.round(currentTime + segmentDuration),
      };
    } else if (parts.length === 1) {
      // 简化格式：只有主标题
      segment = {
        title: parts[0],
        startMs: Math.round(currentTime),
        endMs: Math.round(currentTime + segmentDuration),
      };
    } else {
      // 部分格式：主标题|副标题
      segment = {
        title: parts[0],
        subtitle: parts[1] || '',
        startMs: Math.round(currentTime),
        endMs: Math.round(currentTime + segmentDuration),
      };
    }

    currentTime += segmentDuration;
    return segment;
  });

  return segments;
}

// 主渲染流程
async function main() {
  const config = parseArgs();

  if (!config.text) {
    console.error('错误: 请提供文案内容 --text="你的文案"');
    process.exit(1);
  }

  console.log('='.repeat(50));
  console.log('txt-video 文案视频生成器');
  console.log('='.repeat(50));
  console.log(`文案: ${config.text.substring(0, 50)}...`);
  console.log(`风格: style-1-black (锁死)`);
  console.log(`语速: ${config.speed}x`);
  console.log('='.repeat(50));

  try {
    // 1. 生成语音
    console.log('\n[步骤1] 生成语音...');
    const audioPath = await generateAudio(config.text, { speed: config.speed });

    // 2. 获取音频时长
    console.log('\n[步骤2] 获取音频时长...');
    const audioDuration = await getAudioDuration(audioPath);
    console.log(`[RENDER] 音频时长: ${audioDuration.toFixed(2)}秒`);

    if (audioDuration <= 0) {
      throw new Error('音频时长无效');
    }

    // 3. 计算视频参数
    const fps = 30;
    const durationInFrames = Math.ceil(audioDuration * fps);
    const totalDurationMs = audioDuration * 1000;
    console.log(`[RENDER] 视频时长: ${durationInFrames}帧 (${audioDuration.toFixed(2)}秒)`);

    // 4. 获取背景图
    console.log('\n[步骤3] 获取背景图...');
    await getBackground({ style: 'style-1-black', inputCount: 0 }); // 🔒 锁死风格

    // 5. 解析文案为段落
    console.log('\n[步骤4] 解析文案...');
    const segments = parseTextToSegments(config.text, totalDurationMs);
    console.log(`[RENDER] 文案分段: ${segments.length}段`);

    // 6. 渲染视频
    console.log('\n[步骤5] 渲染视频...');

    // 🔒 锁死风格映射 - 只允许 style-1-black
    const styleMap = {
      'style-1-black': 'Style1Black',
      // style-2-art 和 style-3-gradient 已禁用
    };
    const compositionId = 'Style1Black'; // 强制使用 Style1Black

    // 清除缓存
    const cacheDir = path.join(__dirname, '.remotion');
    if (fs.existsSync(cacheDir)) {
      fs.rmSync(cacheDir, { recursive: true });
    }

    // ⚠️ 格式锁死 - 禁止修改以下参数
    const LOCKED_PROPS = {
      backgroundOpacity: 0.6,
      titleSize: 80,
      subtitleSize: 42,
      contentTop: "28%",
      audioFile: "voiceover.wav",
      backgroundImage: "bg1.png",
    };

    const props = {
      segments: segments,
      ...LOCKED_PROPS,
    };
    const propsJson = JSON.stringify(props, null, 2);

    // 将props写入临时文件，避免命令行参数转义问题
    const propsFile = 'temp-props.json';
    fs.writeFileSync(propsFile, propsJson);

    const renderCmd = `npx remotion render ${compositionId} ${config.output} --codec h264 --quality 80 --duration ${durationInFrames} --props ${propsFile}`;
    console.log(`执行: ${renderCmd}`);

    execSync(renderCmd, {
      cwd: __dirname,
      stdio: 'inherit',
      timeout: 300000,
    });

    // 删除临时文件
    fs.unlinkSync(propsFile);

    console.log('\n' + '='.repeat(50));
    console.log('✅ 视频生成完成!');
    console.log(`输出文件: ${config.output}`);
    console.log(`视频时长: ${audioDuration.toFixed(2)}秒`);
    console.log('='.repeat(50));

    execSync(`open ${config.output}`, { stdio: 'ignore' });

  } catch (error) {
    // 确保删除临时文件
    if (fs.existsSync(propsFile)) {
      fs.unlinkSync(propsFile);
    }
    console.error('\n❌ 错误:', error.message);
    process.exit(1);
  }
}

main();
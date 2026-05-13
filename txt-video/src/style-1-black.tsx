import React from "react";
import { useCurrentFrame, useVideoConfig, AbsoluteFill, Audio, staticFile, spring } from "remotion";

// style-1-black - 可配置的海报风格（分段切换）
// 配置项：图片、文案数组、透明度、字号

interface ContentSegment {
  keyword?: string;
  title: string;
  subtitle?: string;
  quote?: string;
  startMs: number;
  endMs: number;
}

interface Style1BlackProps {
  // 内容配置 - 分段数组
  segments: ContentSegment[];

  // 样式配置
  backgroundImage?: string;
  backgroundOpacity?: number;
  titleSize?: number;
  subtitleSize?: number;
  contentTop?: string;
  audioFile?: string;
}

// 获取当前段落
function getCurrentSegment(segments: ContentSegment[], currentTimeMs: number): ContentSegment {
  for (const segment of segments) {
    if (currentTimeMs >= segment.startMs && currentTimeMs < segment.endMs) {
      return segment;
    }
  }
  return segments[0];
}

export const Style1Black: React.FC<Style1BlackProps> = ({
  segments,
  backgroundImage = "bg1.png",
  backgroundOpacity = 0.6,
  titleSize = 80,
  subtitleSize = 42,
  contentTop = "28%",
  audioFile = "voiceover.wav",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeMs = (frame / fps) * 1000;

  // 获取当前段落
  const currentSegment = getCurrentSegment(segments, currentTimeMs);
  const segmentIndex = segments.findIndex(s => s === currentSegment);

  // 段落切换动画
  const segmentStartFrame = Math.floor(currentSegment.startMs / 1000 * fps);
  const fadeIn = spring({
    frame: frame - segmentStartFrame,
    fps,
    config: { damping: 20, stiffness: 100, mass: 0.5 },
  });

  const slideUp = spring({
    frame: frame - segmentStartFrame,
    fps,
    config: { damping: 25, stiffness: 80, mass: 0.6 },
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0a0a" }}>
      {/* ========== 背景图片 ========== */}
      <AbsoluteFill>
        <img
          src={staticFile(backgroundImage)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: `brightness(${backgroundOpacity}) saturate(1.3) contrast(1.1)`,
          }}
        />
      </AbsoluteFill>

      {/* 渐变遮罩 */}
      <AbsoluteFill
        style={{
          background: "linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.2) 20%, rgba(0,0,0,0.5) 40%, rgba(10,10,10,0.9) 70%, #0a0a0a 100%)",
        }}
      />

      {/* ========== 文字区域 ========== */}
      <AbsoluteFill
        style={{
          top: contentTop,
          left: "5%",
          right: "5%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          opacity: fadeIn,
        }}
      >
        {/* 关键词 */}
        {currentSegment.keyword && (
          <span
            style={{
              fontFamily: "'PingFang SC', 'Microsoft YaHei', 'STHeiti', sans-serif",
              fontSize: 14,
              fontWeight: 400,
              color: "rgba(255,255,255,0.6)",
              letterSpacing: 8,
              marginBottom: 25,
            }}
          >
            {currentSegment.keyword}
          </span>
        )}

        {/* 主标题 */}
        <h1
          style={{
            fontFamily: "'PingFang SC', 'Microsoft YaHei', 'STHeiti', sans-serif",
            fontSize: titleSize,
            fontWeight: 900,
            color: "#FFFFFF",
            textAlign: "center",
            lineHeight: 1.2,
            letterSpacing: 3,
            margin: 0,
            marginBottom: 8,
            textShadow: "0 8px 40px rgba(0,0,0,0.6)",
            transform: `translateY(${(1 - slideUp) * 30}px)`,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            maxWidth: "90%",
          }}
        >
          {currentSegment.title}
        </h1>

        {/* 副标题 */}
        {currentSegment.subtitle && (
          <p
            style={{
              fontFamily: "'PingFang SC', 'Microsoft YaHei', 'STHeiti', sans-serif",
              fontSize: subtitleSize,
              fontWeight: 200,
              color: "rgba(255,255,255,0.85)",
              textAlign: "center",
              letterSpacing: 8,
              margin: 0,
              marginBottom: 30,
            }}
          >
            {currentSegment.subtitle}
          </p>
        )}

        {/* 装饰线 */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 15,
            marginBottom: 30,
          }}
        >
          <div style={{ width: 60, height: 1, backgroundColor: "rgba(255,255,255,0.3)" }} />
          <div style={{ width: 8, height: 8, backgroundColor: "#d4af37", borderRadius: 4 }} />
          <div style={{ width: 60, height: 1, backgroundColor: "rgba(255,255,255,0.3)" }} />
        </div>

        {/* 引用文字 */}
        {currentSegment.quote && (
          <p
            style={{
              fontFamily: "'PingFang SC', 'Microsoft YaHei', 'STHeiti', serif",
              fontSize: 20,
              fontWeight: 300,
              fontStyle: "italic",
              color: "rgba(255,255,255,0.65)",
              textAlign: "center",
              lineHeight: 1.6,
              letterSpacing: 1,
              margin: 0,
              maxWidth: "80%",
            }}
          >
            "{currentSegment.quote}"
          </p>
        )}
      </AbsoluteFill>

      {/* ========== 底部进度 ========== */}
      <AbsoluteFill
        style={{
          bottom: "4%",
          left: "5%",
          right: "5%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ display: "flex", gap: 6 }}>
          {segments.map((_, i) => (
            <div
              key={i}
              style={{
                width: i === segmentIndex ? 24 : 8,
                height: 8,
                borderRadius: 4,
                backgroundColor: i === segmentIndex ? "#d4af37" : "rgba(255,255,255,0.2)",
              }}
            />
          ))}
        </div>
      </AbsoluteFill>

      {/* 音频 */}
      <Audio src={staticFile(audioFile)} />
    </AbsoluteFill>
  );
};
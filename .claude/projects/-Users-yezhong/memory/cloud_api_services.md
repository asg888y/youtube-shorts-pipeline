---
name: cloud api services
description: OCR and Whisper API services deployed on 8.138.165.244
type: reference
originSessionId: 817fda31-43f3-4801-b585-b59ecfe10420
---
OCR and Whisper APIs are deployed on cloud server 8.138.165.244 (2c4g).

**API Endpoints:**
- Umi-OCR (PaddleOCR): `http://8.138.165.244:80/umi-ocr/api/ocr` (POST JSON, base64) — PaddleOCR engine
- Umi-OCR PDF: `http://8.138.165.244:80/umi-ocr/api/doc/upload` (POST multipart)
- Whisper: `http://8.138.165.244:80/whisper/v1/audio/transcriptions` (POST multipart) — faster-whisper tiny int8

**Server Management:**
- SSH: `sshpass -p 'Good5188' ssh -o StrictHostKeyChecking=no root@8.138.165.244`
- Umi-OCR: docker restart umi-ocr / docker logs umi-ocr
- Whisper: systemctl restart whisper-api
- Nginx config: /etc/nginx/sites-available/api-gateway
- Umi-OCR port: 1224 (Docker container)

**Docs:** ~/video_creator/docs/OpenClaw_API接入指南.md

/**
 * QrScannerComponent — Camera-based QR code scanner for the terrain page.
 *
 * Props:
 *   active   {boolean}  — Whether the camera should be running.
 *   onScan   {function} — Called with the decoded string when a QR code is detected.
 *   onError  {function} — Called with an error message string on failure.
 */
import { useEffect, useRef, useCallback } from "react";

export function QrScannerComponent({ active = false, onScan, onError, ...props }) {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const rafRef = useRef(null);
    const streamRef = useRef(null);

    const stopCamera = useCallback(() => {
        if (rafRef.current) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((t) => t.stop());
            streamRef.current = null;
        }
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
    }, []);

    useEffect(() => {
        if (!active) {
            stopCamera();
            return;
        }

        let cancelled = false;

        const startScanner = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: { ideal: "environment" } },
                });
                if (cancelled) {
                    stream.getTracks().forEach((t) => t.stop());
                    return;
                }
                streamRef.current = stream;
                const video = videoRef.current;
                if (!video) return;
                video.srcObject = stream;
                await video.play();

                const tick = () => {
                    if (cancelled) return;
                    const canvas = canvasRef.current;
                    if (!canvas || !video || video.readyState < 2) {
                        rafRef.current = requestAnimationFrame(tick);
                        return;
                    }
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    const ctx = canvas.getContext("2d", { willReadFrequently: true });
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

                    // jsQR is expected to be loaded via rx.script from /assets/jsQR.min.js
                    if (window.jsQR) {
                        const code = window.jsQR(imageData.data, imageData.width, imageData.height, {
                            inversionAttempts: "dontInvert",
                        });
                        if (code && code.data) {
                            if (onScan) onScan(code.data);
                        }
                    }
                    rafRef.current = requestAnimationFrame(tick);
                };
                rafRef.current = requestAnimationFrame(tick);
            } catch (err) {
                if (!cancelled && onError) {
                    onError(err.message || "Camera error");
                }
            }
        };

        startScanner();

        return () => {
            cancelled = true;
            stopCamera();
        };
    }, [active, onScan, onError, stopCamera]);

    return (
        <div
            style={{
                position: "relative",
                width: "100%",
                maxWidth: "360px",
                margin: "0 auto",
                borderRadius: "8px",
                overflow: "hidden",
                background: "#000",
                aspectRatio: "1 / 1",
                ...props.style,
            }}
        >
            <video
                ref={videoRef}
                playsInline
                muted
                style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
            />
            <canvas ref={canvasRef} style={{ display: "none" }} />
            {/* Scanning overlay */}
            <div
                style={{
                    position: "absolute",
                    inset: 0,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    pointerEvents: "none",
                }}
            >
                <div
                    style={{
                        width: "65%",
                        height: "65%",
                        border: "3px solid rgba(99,221,99,0.85)",
                        borderRadius: "12px",
                        boxShadow: "0 0 0 9999px rgba(0,0,0,0.35)",
                    }}
                />
            </div>
        </div>
    );
}

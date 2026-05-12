"""
Audio Processor Module
Extracts acoustic features using Librosa and computes stress score (0-100).
"""

import numpy as np
import io


def extract_features(audio_bytes: bytes, sample_rate: int = 22050) -> dict:
    try:
        import librosa
        audio_buffer = io.BytesIO(audio_bytes)
        y, sr = librosa.load(audio_buffer, sr=sample_rate, mono=True)
        if len(y) < sr * 0.5:
            return None
        duration = len(y) / sr
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_std = np.std(mfccs, axis=1)
        f0, voiced_flag, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7")
        )
        voiced_f0 = f0[voiced_flag] if voiced_flag is not None else np.array([])
        pitch_std = float(np.nanstd(voiced_f0)) if len(voiced_f0) > 0 else 20.0
        rms = librosa.feature.rms(y=y)[0]
        energy_std = float(np.std(rms))
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        speech_rate = float(np.mean(zcr) * sr / 512)
        return {
            "mfcc_variance": float(np.mean(mfcc_std ** 2)),
            "pitch_std": pitch_std,
            "energy_std": energy_std,
            "speech_rate": speech_rate,
            "duration": duration,
        }
    except Exception as e:
        print(f"Feature extraction error: {e}")
        return None


def compute_stress_score(features: dict) -> float:
    if features is None:
        return 50.0
    score = 0.0
    score += min(30, (features.get("mfcc_variance", 0) / 15))
    score += min(30, (features.get("pitch_std", 0) / 3.5))
    score += min(20, (features.get("energy_std", 0) * 800))
    speech_rate = features.get("speech_rate", 5)
    if speech_rate > 9:
        score += min(20, (speech_rate - 9) * 5)
    elif speech_rate < 2:
        score += min(20, (2 - speech_rate) * 10)
    return round(min(100, max(0, score)), 1)


def get_stress_level(score: float) -> tuple:
    if score < 30:
        return ("Calm", "#28a745", "😊")
    elif score < 55:
        return ("Moderate", "#ffc107", "😐")
    elif score < 75:
        return ("Elevated", "#fd7e14", "😰")
    else:
        return ("High Stress", "#dc3545", "😨")


def get_recovery_prompt(score: float) -> str | None:
    import random
    if score >= 75:
        return random.choice([
            "🌬️ Take a deep breath — inhale for 4 seconds, exhale slowly.",
            "🐢 Slow down your pace. Speak clearly, not quickly.",
            "💪 You know this material. Take a moment before answering.",
        ])
    elif score >= 55:
        return random.choice([
            "📢 Increase your volume slightly — speak with confidence.",
            "🎯 Focus on one key point at a time.",
            "👏 You are doing well — stay focused and steady.",
        ])
    return None

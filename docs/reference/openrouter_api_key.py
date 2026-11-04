"""OpenRouter API-kulcs – CSAK környezeti változóból.

A korábban itt tárolt kulcsok nyilvánosságra kerültek (2026-11-04-i ellenőrzés); vissza kell vonni őket.
Kulcs SOHA nem kerülhet a repóba. Beállítás: lásd config/openrouter.env.example.
"""
import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

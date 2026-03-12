"""
Client Claude via la CLI `claude` — aucune clé API requise.

Utilise l'abonnement Claude Code (Pro/Max) de l'utilisateur déjà authentifié.
Compatible avec les mêmes patterns que l'API Anthropic (messages, system, etc.)

Prérequis :
  - `claude` installé (npm install -g @anthropic-ai/claude-code)
  - Authentifié : claude auth login
"""

import json
import os
import subprocess
import time
from typing import Any


# Modèle par défaut (ignoré par la CLI qui utilise celui configuré)
DEFAULT_MODEL = "claude-sonnet-4-6"

# Timeout par défaut pour les appels CLI (secondes)
DEFAULT_TIMEOUT = 300


class _FakeUsage:
    """Mime l'objet `usage` de l'API Anthropic (pour compatibilité)."""
    input_tokens = 0
    output_tokens = 0


class _FakeMessage:
    """
    Mime l'objet `Message` retourné par l'API Anthropic.
    Permet de remplacer la CLI sans changer le code des agents.
    """
    def __init__(self, text: str):
        self._text = text
        self.model = DEFAULT_MODEL
        self.stop_reason = "end_turn"
        self.usage = _FakeUsage()
        self.content = [type("Block", (), {"text": text})()]

    def __str__(self):
        return self._text


class ClaudeCliClient:
    """
    Remplaçant de `anthropic.Anthropic()` qui passe par la CLI `claude`.

    Usage (identique à l'API Anthropic) :
        client = ClaudeCliClient()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system="Tu es un assistant...",
            messages=[{"role": "user", "content": "Bonjour"}],
        )
        texte = response.content[0].text
    """

    def __init__(self):
        self.messages = _MessagesClient()


class _MessagesClient:
    """Sous-client pour `client.messages.create(...)`."""

    def create(
        self,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 4000,
        system: str = "",
        messages: list[dict] = None,
        temperature: float = 1.0,
        **kwargs,
    ) -> _FakeMessage:
        """
        Appelle `claude --print` avec le prompt construit depuis messages + system.
        Retourne un objet compatible `anthropic.types.Message`.
        """
        prompt = _construire_prompt(system=system, messages=messages or [])
        texte = _appeler_cli(prompt, timeout=max(DEFAULT_TIMEOUT, max_tokens // 4))
        return _FakeMessage(texte)


# ── Construction du prompt ─────────────────────────────────────────────────────

def _construire_prompt(system: str, messages: list[dict]) -> str:
    """
    Combine le system prompt et les messages en un prompt texte unique.
    Respecte le format attendu par la CLI claude.
    """
    parties = []

    if system:
        parties.append(f"<system>\n{system.strip()}\n</system>")

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # Le contenu peut être une liste de blocs (tool use, texte, etc.)
        if isinstance(content, list):
            textes = []
            for bloc in content:
                if isinstance(bloc, dict):
                    if bloc.get("type") == "text":
                        textes.append(bloc.get("text", ""))
                    elif bloc.get("type") == "tool_result":
                        textes.append(str(bloc.get("content", "")))
                else:
                    textes.append(str(bloc))
            content = "\n".join(textes)

        if role == "assistant":
            parties.append(f"<assistant>\n{content}\n</assistant>")
        else:
            parties.append(content)

    return "\n\n".join(parties)


# ── Appel CLI ─────────────────────────────────────────────────────────────────

def _appeler_cli(prompt: str, timeout: int = DEFAULT_TIMEOUT, retries: int = 3) -> str:
    """
    Appelle `claude --print` avec le prompt donné.
    Gère les erreurs et retries avec backoff exponentiel.
    """
    cmd = ["claude", "--print", "--output-format", "text"]

    for tentative in range(retries):
        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    return output
                # Stdout vide = erreur silencieuse
                raise RuntimeError(
                    f"claude CLI: sortie vide (stderr: {result.stderr[:200]})"
                )

            stderr = result.stderr.strip()
            raise RuntimeError(f"claude CLI code {result.returncode}: {stderr[:300]}")

        except subprocess.TimeoutExpired:
            if tentative == retries - 1:
                raise RuntimeError(f"claude CLI timeout après {timeout}s")
            attente = 2 ** tentative
            print(f"  ⚠️  Timeout CLI (tentative {tentative + 1}/{retries}), retry dans {attente}s…")
            time.sleep(attente)

        except FileNotFoundError:
            raise RuntimeError(
                "Commande `claude` introuvable. "
                "Installez Claude Code : npm install -g @anthropic-ai/claude-code "
                "puis authentifiez-vous : claude auth login"
            )

        except RuntimeError:
            if tentative == retries - 1:
                raise
            attente = 2 ** tentative
            time.sleep(attente)

    return ""


# ── Compatibilité directe pour les agents ─────────────────────────────────────

def appeler_claude(
    prompt: str,
    system: str = "",
    max_tokens: int = 4000,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    Interface simplifiée pour appeler Claude via CLI.
    Retourne directement le texte de la réponse.
    """
    full_prompt = _construire_prompt(system=system, messages=[{"role": "user", "content": prompt}])
    return _appeler_cli(full_prompt, timeout=max(timeout, max_tokens // 4))


def verifier_cli_disponible() -> bool:
    """Vérifie que la commande `claude` est disponible et authentifiée."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"  ✅ Claude CLI disponible : {result.stdout.strip()}")
            return True
        print("  ❌ Claude CLI non disponible")
        return False
    except FileNotFoundError:
        print("  ❌ `claude` introuvable — installez Claude Code et authentifiez-vous")
        return False
    except Exception as exc:
        print(f"  ❌ Erreur vérification claude CLI : {exc}")
        return False

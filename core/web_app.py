import json
from flask import Flask, render_template_string, request, jsonify
from loguru import logger

# Головна HTML-сторінка (стилізована під лаву, з можливістю зміни теми)
MAIN_HTML = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arma Reforger Bot</title>
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #ff5000 0%, #c800c8 50%, #00c8ff 100%);
            --card-bg: rgba(20, 0, 0, 0.85);
            --text-color: #ffaa00;
            --btn-bg: linear-gradient(135deg, #ff4400, #ff8800);
            --btn-hover: linear-gradient(135deg, #ff6600, #ffaa00);
            --input-bg: #330000;
            --input-border: #ff6600;
            --input-text: #ffcc00;
            --tab-active: linear-gradient(180deg, #ff6600, #cc3300);
            --progress-bg: #330000;
            --progress-chunk: linear-gradient(90deg, #ff4400, #ff8800);
        }

        [data-theme="neon"] {
            --bg-gradient: linear-gradient(135deg, #00ffc8 0%, #ff00ff 50%, #00c8ff 100%);
            --card-bg: rgba(0, 20, 30, 0.85);
            --text-color: #00ffcc;
            --btn-bg: linear-gradient(135deg, #00ffcc, #ff00ff);
            --btn-hover: linear-gradient(135deg, #00ffff, #ff33ff);
            --input-bg: #001a33;
            --input-border: #ff00ff;
            --input-text: #00ffcc;
            --tab-active: linear-gradient(180deg, #00ffcc, #0099aa);
            --progress-bg: #001a33;
            --progress-chunk: linear-gradient(90deg, #00ffcc, #ff00ff);
        }

        [data-theme="cyberpunk"] {
            --bg-gradient: linear-gradient(135deg, #ff0099 0%, #6600cc 50%, #00ff00 100%);
            --card-bg: rgba(10, 10, 10, 0.9);
            --text-color: #ff0099;
            --btn-bg: linear-gradient(135deg, #ff0099, #6600cc);
            --btn-hover: linear-gradient(135deg, #ff33aa, #9933ff);
            --input-bg: #111;
            --input-border: #ff0099;
            --input-text: #00ff00;
            --tab-active: linear-gradient(180deg, #ff0099, #9933ff);
            --progress-bg: #111;
            --progress-chunk: linear-gradient(90deg, #ff0099, #6600cc);
        }

        [data-theme="classic"] {
            --bg-gradient: linear-gradient(135deg, #f0f0f0 0%, #c8c8c8 50%, #969696 100%);
            --card-bg: rgba(240, 240, 240, 0.9);
            --text-color: #333;
            --btn-bg: linear-gradient(135deg, #e0e0e0, #c0c0c0);
            --btn-hover: linear-gradient(135deg, #d0d0d0, #b0b0b0);
            --input-bg: #fff;
            --input-border: #888;
            --input-text: #000;
            --tab-active: linear-gradient(180deg, #d0d0d0, #b0b0b0);
            --progress-bg: #ddd;
            --progress-chunk: linear-gradient(90deg, #c0c0c0, #a0a0a0);
        }

        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-gradient);
            color: var(--text-color);
            min-height: 100vh;
        }

        .container {
            max-width: 500px;
            margin: 0 auto;
            padding: 15px;
        }

        h1 {
            text-align: center;
            font-size: 24px;
            margin: 10px 0 20px;
            color: white;
            text-shadow: 0 0 10px rgba(0,0,0,0.5);
        }

        .card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid var(--input-border);
        }

        button {
            background: var(--btn-bg);
            color: white;
            border: 1px solid var(--input-border);
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 14px;
            margin: 5px;
            cursor: pointer;
            width: calc(100% - 20px);
        }

        button:hover {
            background: var(--btn-hover);
        }

        button.small {
            width: auto;
            padding: 8px 12px;
            font-size: 13px;
        }

        select, input {
            background: var(--input-bg);
            color: var(--input-text);
            border: 1px solid var(--input-border);
            padding: 8px;
            border-radius: 6px;
            width: 100%;
            margin: 5px 0;
            box-sizing: border-box;
        }

        .progress-bar {
            background: var(--progress-bg);
            border: 1px solid var(--input-border);
            border-radius: 6px;
            height: 20px;
            margin: 5px 0;
            overflow: hidden;
        }

        .progress-fill {
            background: var(--progress-chunk);
            height: 100%;
            width: 0%;
            transition: width 0.5s;
        }

        .status-row {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
        }

        .log {
            background: rgba(0,0,0,0.3);
            border-radius: 6px;
            padding: 10px;
            max-height: 150px;
            overflow-y: auto;
            font-size: 12px;
            margin-top: 10px;
        }

        .btn-group {
            display: flex;
            gap: 5px;
        }

        .theme-selector {
            display: flex;
            justify-content: center;
            gap: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 Arma Reforger Bot</h1>

        <div class="theme-selector">
            <button class="small" onclick="setTheme('lava')">🌋 Лава</button>
            <button class="small" onclick="setTheme('neon')">💡 Неон</button>
            <button class="small" onclick="setTheme('cyberpunk')">🤖 Кіберпанк</button>
            <button class="small" onclick="setTheme('classic')">📜 Класика</button>
        </div>

        <div class="card">
            <div class="status-row">
                <span>Стан гри:</span>
                <span id="gameState">невідомо</span>
            </div>
            <div class="status-row">
                <span>Черга сервера:</span>
                <span id="queuePos">N/A</span>
            </div>
            <div>Прогрес черги:</div>
            <div class="progress-bar">
                <div class="progress-fill" id="queueBar"></div>
            </div>
        </div>

        <div class="card">
            <button onclick="apiCall('/api/automation/toggle')">🤖 Старт/Стоп авто</button>
            <button onclick="apiCall('/api/connect')">🔌 Підключитись зараз</button>
            <button onclick="apiCall('/api/screenshot')">📸 Скріншот</button>
        </div>

        <div class="card">
            <div>Список плагінів:</div>
            <div id="pluginsList"></div>
        </div>

        <div class="log" id="logOutput">
            Чекаю на дії...
        </div>
    </div>

    <script>
        let currentTheme = localStorage.getItem('theme') || 'lava';
        setTheme(currentTheme);

        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
        }

        async function apiCall(endpoint, method = 'GET', body = null) {
            try {
                const options = { method };
                if (body) {
                    options.headers = { 'Content-Type': 'application/json' };
                    options.body = JSON.stringify(body);
                }
                const response = await fetch(endpoint, options);
                const data = await response.json();
                addLog(data.message || JSON.stringify(data));
                updateDashboard();
            } catch (err) {
                addLog('Помилка: ' + err.message);
            }
        }

        function addLog(msg) {
            const log = document.getElementById('logOutput');
            log.innerHTML += '<br>' + new Date().toLocaleTimeString() + ': ' + msg;
            log.scrollTop = log.scrollHeight;
        }

        async function updateDashboard() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('gameState').textContent = data.game_state || '?';
                document.getElementById('queuePos').textContent = data.queue_position || 'N/A';
                const bar = document.getElementById('queueBar');
                bar.style.width = Math.min((data.queue_position / 100) * 100, 100) + '%';
            } catch(e) {}
        }

        async function loadPlugins() {
            try {
                const res = await fetch('/api/plugins');
                const data = await res.json();
                let html = '';
                data.plugins.forEach(p => {
                    html += `<div class="status-row">
                        <span>${p.name}</span>
                        <button class="small" onclick="togglePlugin('${p.name}')">${p.enabled ? '✅' : '❌'}</button>
                    </div>`;
                });
                document.getElementById('pluginsList').innerHTML = html || 'Плагіни не знайдено';
            } catch(e) {}
        }

        async function togglePlugin(name) {
            await apiCall('/api/plugins/toggle', 'POST', { name });
            loadPlugins();
        }

        setInterval(updateDashboard, 5000);
        updateDashboard();
        loadPlugins();
    </script>
</body>
</html>
"""

class WebServer:
    def __init__(self, config, game_controller, automation, plugin_manager, license_manager, telegram_bot):
        self.app = Flask(__name__)
        self.config = config
        self.game_controller = game_controller
        self.automation = automation
        self.plugin_manager = plugin_manager
        self.license_manager = license_manager
        self.telegram_bot = telegram_bot

        # Маршрути
        self.app.route('/')(self.index)
        self.app.route('/api/status')(self.api_status)
        self.app.route('/api/automation/toggle')(self.api_toggle_automation)
        self.app.route('/api/connect')(self.api_connect)
        self.app.route('/api/screenshot')(self.api_screenshot)
        self.app.route('/api/plugins')(self.api_plugins_list)
        self.app.route('/api/plugins/toggle', methods=['POST'])(self.api_toggle_plugin)

    def index(self):
        return render_template_string(MAIN_HTML)

    def api_status(self):
        state = self.game_controller.get_game_state()
        queue = self.game_controller.get_queue_position()
        return jsonify({
            "game_state": state,
            "queue_position": queue
        })

    def api_toggle_automation(self):
        if self.automation.running:
            self.automation.stop()
            msg = "Автоматизацію зупинено"
        else:
            self.automation.start()
            msg = "Автоматизацію запущено"
        return jsonify({"message": msg})

    def api_connect(self):
        if not self.license_manager.is_pro():
            return jsonify({"message": "Потрібна Pro-версія"})
        # Запускаємо підключення у фоновому потоці
        import threading
        def connect():
            from core.adaptive_connector import AdaptiveConnector
            connector = AdaptiveConnector(self.config)
            result = connector.connect()
            logger.info(f"Web connect result: {result}")
        threading.Thread(target=connect, daemon=True).start()
        return jsonify({"message": "Підключення запущено..."})

    def api_screenshot(self):
        from PIL import ImageGrab
        import io
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        if self.telegram_bot and self.telegram_bot.bot:
            self.telegram_bot.bot.send_photo(
                self.config.get("admin_chat_id", 390469052),
                buf,
                caption="📸 Скріншот через Web App"
            )
        return jsonify({"message": "Скріншот відправлено в Telegram"})

    def api_plugins_list(self):
        plugins = self.plugin_manager.get_plugin_list()
        return jsonify({
            "plugins": [{"name": p.get_name(), "enabled": p.is_enabled()} for p in plugins]
        })

    def api_toggle_plugin(self):
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({"message": "Ім'я плагіна не вказано"})
        plugin = self.plugin_manager.plugins.get(name)
        if not plugin:
            return jsonify({"message": "Плагін не знайдено"})
        if plugin.is_enabled():
            self.plugin_manager.disable_plugin(name)
            return jsonify({"message": f"Плагін '{name}' вимкнено"})
        else:
            if not self.license_manager.is_pro():
                return jsonify({"message": "Потрібна Pro-версія"})
            success = self.plugin_manager.enable_plugin(name)
            return jsonify({"message": f"Плагін '{name}' увімкнено" if success else "Помилка"})

    def run(self, host='0.0.0.0', port=5000):
        self.app.run(host=host, port=port, debug=False, use_reloader=False)
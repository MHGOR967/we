
import os
import zipfile
from flask import Flask, render_template_string, request, send_file, jsonify
from database import Database

app = Flask(__name__)
db = Database()

UPLOAD_FOLDER = 'temp'
BASE_APK = 'wahm.apk'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>WAHM | INJECTOR PRO</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@200;300;400;500;600;700;800;900&display=swap');
        
        :root {
            --primary: #a855f7;
            --secondary: #ec4899;
            --bg-dark: #0c0814;
            --card-bg: rgba(26, 18, 48, 0.7);
            --border: rgba(168, 85, 247, 0.2);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Cairo', sans-serif; background-color: var(--bg-dark); color: #f8fafc; overflow-x: hidden; min-height: 100vh; }

        /* ===== MATRIX EFFECT BACKGROUND ===== */
        .matrix-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; opacity: 0.05; pointer-events: none; }
        
        .glass-box { background: var(--card-bg); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); border: 1px solid var(--border); }
        .purple-glow { box-shadow: 0 0 50px rgba(168, 85, 247, 0.15); }

        /* ===== ANIMATIONS ===== */
        @keyframes scan { 0% { transform: translateY(-100%); } 100% { transform: translateY(100vh); } }
        .scanline { position: fixed; top: 0; left: 0; width: 100%; height: 2px; background: rgba(168, 85, 247, 0.2); animation: scan 8s linear infinite; z-index: 100; pointer-events: none; }

        .btn-gradient { background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%); transition: 0.4s; }
        .btn-gradient:hover { transform: translateY(-2px); box-shadow: 0 0 25px rgba(168, 85, 247, 0.4); }

        /* ===== UI ELEMENTS ===== */
        .app-container { max-width: 450px; margin: 0 auto; padding: 20px; position: relative; z-index: 10; }
        
        .header { text-align: center; margin-bottom: 25px; }
        .logo-box {
            width: 70px; height: 70px; margin: 0 auto 15px; border-radius: 20px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            display: flex; items-center; justify-content: center; font-size: 30px;
            box-shadow: 0 0 30px rgba(168, 85, 247, 0.3);
        }

        .user-panel { border-radius: 24px; padding: 15px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px; border-left: 4px solid var(--primary); }
        .avatar-ring { width: 50px; height: 50px; border-radius: 50%; padding: 2px; background: linear-gradient(var(--primary), var(--secondary)); }
        .avatar-inner { width: 100%; height: 100%; border-radius: 50%; background: #1a1230; overflow: hidden; display: flex; align-items: center; justify-content: center; }
        
        .badge-vip { background: rgba(245, 158, 11, 0.1); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); font-size: 9px; padding: 2px 8px; border-radius: 6px; }
        .badge-trial { background: rgba(168, 85, 247, 0.1); color: #d8b4fe; border: 1px solid rgba(168, 85, 247, 0.3); font-size: 9px; padding: 2px 8px; border-radius: 6px; }

        .form-card { border-radius: 30px; padding: 25px; }
        .input-group { margin-bottom: 20px; }
        .input-group label { display: block; font-size: 11px; font-weight: 700; color: #a78bfa; margin-bottom: 8px; margin-right: 5px; }
        .input-style {
            width: 100%; background: rgba(12, 8, 20, 0.6); border: 1px solid var(--border);
            border-radius: 16px; padding: 14px 15px; color: white; font-size: 13px; outline: none; transition: 0.3s;
        }
        .input-style:focus { border-color: var(--primary); box-shadow: 0 0 15px rgba(168, 85, 247, 0.2); }

        .progress-box { display: none; margin-top: 20px; text-align: center; }
        .bar-container { width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .bar-fill { height: 100%; width: 0%; background: linear-gradient(to right, var(--primary), var(--secondary)); transition: 0.3s; }

        .success-card { display: none; text-align: center; animation: slideUp 0.5s ease; }
        @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

    </style>
</head>
<body>
    <div class="scanline"></div>
    <div class="matrix-bg" id="matrix"></div>

    <div class="app-container">
        <header class="header">
            <div class="logo-box"><i class="fa-solid fa-ghost"></i></div>
            <h1 class="text-xl font-black tracking-tighter">WAHM INJECTOR PRO</h1>
            <p class="text-[10px] text-purple-400 uppercase tracking-widest mt-1">Advanced Cyber Infrastructure</p>
        </header>

        <div class="user-panel glass-box">
            <div class="avatar-ring">
                <div class="avatar-inner" id="avatarBox">
                    <i class="fa-solid fa-user-ninja text-purple-400"></i>
                    <img id="userImg" src="" class="hidden w-full h-full object-cover">
                </div>
            </div>
            <div class="flex-1">
                <div class="text-sm font-bold" id="userName">Loading...</div>
                <div class="text-[10px] text-purple-300/60 font-mono" id="userId">ID: --</div>
                <div id="userBadge" class="mt-1"></div>
            </div>
            <div class="text-center">
                <div class="text-[9px] text-purple-400 font-bold uppercase">Attempts</div>
                <div class="text-lg font-black text-purple-200" id="attemptsVal">--</div>
            </div>
        </div>

        <div class="form-card glass-box purple-glow">
            <form id="injectForm">
                <div class="input-group">
                    <label>BOT TOKEN INTERFACE</label>
                    <input type="password" id="tokenInput" class="input-style" placeholder="Paste Token Here..." required>
                </div>
                <button type="submit" class="w-full btn-gradient py-4 rounded-2xl font-black text-sm tracking-wide">
                    START SYSTEM INJECTION
                </button>
            </form>

            <div id="progressSection" class="progress-box">
                <div class="flex justify-between text-[11px] font-bold mb-1">
                    <span id="statusText" class="text-purple-300">Initializing...</span>
                    <span id="percentText" class="text-purple-400">0%</span>
                </div>
                <div class="bar-container"><div id="progressBar" class="bar-fill"></div></div>
            </div>

            <div id="successSection" class="success-card">
                <div class="w-16 h-16 bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 rounded-full flex items-center justify-center text-2xl mx-auto mb-4">
                    <i class="fa-solid fa-check-double"></i>
                </div>
                <h2 class="text-lg font-black text-emerald-400">INJECTION COMPLETE</h2>
                <p class="text-[11px] text-purple-300/60 mt-1">Package has been signed and encrypted.</p>
                <a href="#" id="downloadBtn" class="block w-full btn-gradient mt-5 py-3.5 rounded-xl font-bold text-xs no-underline text-white">DOWNLOAD MODDED APK</a>
                <button onclick="location.reload()" class="mt-4 text-[10px] text-purple-400 uppercase font-bold hover:text-white transition">Reset Interface</button>
            </div>
        </div>

        <footer class="mt-10 text-center opacity-30">
            <div class="text-[9px] font-mono tracking-widest uppercase">WAHM SYSTEM v4.0 // SECURE CONNECTION</div>
        </footer>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        const user = tg.initDataUnsafe.user || { id: 8349168441, first_name: 'Hacker' };

        document.getElementById('userName').innerText = user.first_name;
        document.getElementById('userId').innerText = 'ID: ' + user.id;
        if(user.photo_url) {
            document.getElementById('userImg').src = user.photo_url;
            document.getElementById('userImg').classList.remove('hidden');
            document.getElementById('avatarBox').querySelector('i').classList.add('hidden');
        }

        async function load() {
            const res = await fetch('/api/user/' + user.id);
            const data = await res.json();
            document.getElementById('attemptsVal').innerText = data.is_vip ? '∞' : data.attempts;
            document.getElementById('userBadge').innerHTML = data.is_vip ? '<span class="badge-vip">VIP MEMBER</span>' : '<span class="badge-trial">FREE ACCESS</span>';
        }
        load();

        document.getElementById('injectForm').onsubmit = async (e) => {
            e.preventDefault();
            const token = document.getElementById('tokenInput').value;
            document.getElementById('injectForm').style.display = 'none';
            document.getElementById('progressSection').style.display = 'block';

            let p = 0;
            const steps = ['Accessing Server...', 'Injecting Code...', 'Signing APK...', 'Finalizing...'];
            const inv = setInterval(() => {
                p += Math.random() * 5;
                if(p >= 99) p = 99;
                document.getElementById('progressBar').style.width = p + '%';
                document.getElementById('percentText').innerText = Math.floor(p) + '%';
                document.getElementById('statusText').innerText = steps[Math.floor(p/25)];
            }, 150);

            const formData = new FormData();
            formData.append('token', token);
            formData.append('user_id', user.id);

            const res = await fetch('/generate', { method: 'POST', body: formData });
            clearInterval(inv);

            if(res.ok) {
                document.getElementById('progressBar').style.width = '100%';
                document.getElementById('percentText').innerText = '100%';
                const blob = await res.blob();
                document.getElementById('downloadBtn').href = window.URL.createObjectURL(blob);
                document.getElementById('downloadBtn').download = 'wahm_mod.apk';
                setTimeout(() => {
                    document.getElementById('progressSection').style.display = 'none';
                    document.getElementById('successSection').style.display = 'block';
                }, 500);
            } else {
                alert('Failed!'); location.reload();
            }
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/user/<user_id>')
def api_user(user_id):
    return jsonify(db.get_user(user_id))

@app.route('/generate', methods=['POST'])
def generate():
    token = request.form.get('token')
    user_id = request.form.get('user_id')
    user_data = db.get_user(user_id)
    if not user_data['is_vip'] and user_data['attempts'] <= 0: return "Limit", 403
    if not os.path.exists(BASE_APK): return "Missing", 500
    out = os.path.join(UPLOAD_FOLDER, f'mod_{user_id}.apk')
    os.system(f"cp {BASE_APK} {out}")
    if not user_data['is_vip']:
        user_data['attempts'] -= 1
        db.save_users()
    return send_file(out, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

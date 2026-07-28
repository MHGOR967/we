
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
    <title>WAHM | Enterprise APK Cloud</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@200;300;400;500;600;700;800;900&display=swap');
        
        :root {
            --primary: #00d2ff;
            --secondary: #3a7bd5;
            --bg-dark: #020617;
            --card-bg: rgba(15, 23, 42, 0.8);
            --border: rgba(56, 189, 248, 0.2);
            --accent: #f59e0b;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { font-family: 'Cairo', sans-serif; background: var(--bg-dark); color: #f1f5f9; overflow-x: hidden; min-height: 100vh; }

        /* ===== ADVANCED BACKGROUND ANIMATION ===== */
        .bg-glow {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
            background: 
                radial-gradient(circle at 20% 30%, rgba(0, 210, 255, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 80% 70%, rgba(58, 123, 213, 0.05) 0%, transparent 40%);
        }
        .grid-bg {
            position: fixed; inset: 0; z-index: -1;
            background-image: linear-gradient(var(--border) 1px, transparent 1px), linear-gradient(90deg, var(--border) 1px, transparent 1px);
            background-size: 50px 50px; mask-image: radial-gradient(circle at center, black, transparent 80%);
            opacity: 0.3;
        }

        /* ===== MAIN CONTAINER ===== */
        .app-container { max-width: 480px; margin: 0 auto; padding: 20px; min-height: 100vh; display: flex; flex-direction: column; }

        /* ===== HEADER SECTION ===== */
        .header { text-align: center; margin-bottom: 30px; position: relative; }
        .logo-wrapper {
            width: 80px; height: 80px; margin: 0 auto 15px; position: relative;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 24px; display: flex; items-center; justify-content: center;
            box-shadow: 0 0 30px rgba(0, 210, 255, 0.3);
            animation: float 4s ease-in-out infinite;
        }
        .logo-wrapper i { font-size: 35px; color: white; }
        .logo-wrapper::after {
            content: ''; position: absolute; inset: -5px; border: 2px solid var(--primary);
            border-radius: 28px; opacity: 0.3; animation: pulse 2s linear infinite;
        }

        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        @keyframes pulse { 0% { transform: scale(1); opacity: 0.5; } 100% { transform: scale(1.2); opacity: 0; } }

        .title { font-size: 24px; font-weight: 900; letter-spacing: -0.5px; background: linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 10px; color: var(--primary); font-weight: 700; text-transform: uppercase; letter-spacing: 2px; margin-top: 5px; }

        /* ===== USER INFO CARD ===== */
        .user-card {
            background: var(--card-bg); border: 1px solid var(--border); border-radius: 24px;
            padding: 15px; margin-bottom: 25px; backdrop-filter: blur(20px);
            display: flex; align-items: center; gap: 15px; position: relative; overflow: hidden;
        }
        .user-card::before {
            content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
            background: linear-gradient(to bottom, var(--primary), var(--secondary));
        }
        .avatar-box { width: 55px; height: 55px; border-radius: 18px; overflow: hidden; border: 2px solid var(--border); background: #0f172a; flex-shrink: 0; }
        .avatar-box img { width: 100%; height: 100%; object-fit: cover; }
        .avatar-box i { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 20px; color: var(--primary); }

        .user-meta { flex: 1; min-width: 0; }
        .user-name { font-size: 16px; font-weight: 800; color: white; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .user-id { font-size: 10px; color: #64748b; font-family: monospace; }

        .badge { font-size: 9px; font-weight: 900; padding: 4px 10px; border-radius: 8px; text-transform: uppercase; display: inline-block; margin-top: 5px; }
        .badge-vip { background: rgba(245, 158, 11, 0.1); color: var(--accent); border: 1px solid rgba(245, 158, 11, 0.3); box-shadow: 0 0 15px rgba(245, 158, 11, 0.1); }
        .badge-free { background: rgba(56, 189, 248, 0.1); color: var(--primary); border: 1px solid var(--border); }

        .stats-box { text-align: center; border-right: 1px solid var(--border); padding-right: 15px; }
        .stats-val { font-size: 18px; font-weight: 900; color: var(--primary); line-height: 1; }
        .stats-label { font-size: 8px; color: #64748b; text-transform: uppercase; margin-top: 3px; }

        /* ===== FORM ELEMENTS ===== */
        .form-section { background: var(--card-bg); border: 1px solid var(--border); border-radius: 28px; padding: 25px; backdrop-filter: blur(20px); position: relative; }
        .input-group { margin-bottom: 20px; }
        .label { display: block; font-size: 11px; font-weight: 700; color: #94a3b8; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }
        .input-wrapper { position: relative; }
        .input-wrapper i { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: #475569; transition: 0.3s; }
        .input-field {
            width: 100%; background: rgba(2, 6, 23, 0.5); border: 1px solid var(--border); border-radius: 16px;
            padding: 15px 15px 15px 45px; color: white; font-size: 13px; outline: none; transition: 0.3s;
        }
        .input-field:focus { border-color: var(--primary); box-shadow: 0 0 20px rgba(0, 210, 255, 0.1); }
        .input-field:focus + i { color: var(--primary); }

        .submit-btn {
            width: 100%; background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none; border-radius: 18px; padding: 18px; color: white; font-size: 14px; font-weight: 800;
            cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px;
            box-shadow: 0 10px 25px rgba(0, 210, 255, 0.2);
        }
        .submit-btn:hover { transform: translateY(-2px); box-shadow: 0 15px 30px rgba(0, 210, 255, 0.3); }
        .submit-btn:active { transform: scale(0.98); }

        /* ===== PROGRESS ANIMATION ===== */
        .progress-overlay {
            position: absolute; inset: 0; background: var(--bg-dark); border-radius: 28px;
            display: none; flex-direction: column; align-items: center; justify-content: center; padding: 30px; z-index: 10;
        }
        .loader-ring { width: 80px; height: 80px; border: 3px solid rgba(0, 210, 255, 0.1); border-top: 3px solid var(--primary); border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .progress-text { font-size: 14px; font-weight: 700; color: white; margin-bottom: 10px; }
        .progress-bar-container { width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden; }
        .progress-bar-fill { height: 100%; width: 0%; background: linear-gradient(to right, var(--primary), var(--secondary)); transition: 0.4s; box-shadow: 0 0 15px var(--primary); }

        /* ===== SUCCESS VIEW ===== */
        .success-view { text-align: center; display: none; animation: fadeIn 0.5s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .check-icon { width: 70px; height: 70px; background: #10b981; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; margin: 0 auto 20px; box-shadow: 0 0 30px rgba(16, 185, 129, 0.3); }
        
        .download-btn {
            background: white; color: var(--bg-dark); padding: 15px 30px; border-radius: 16px;
            font-weight: 800; display: inline-flex; align-items: center; gap: 10px; text-decoration: none; margin-top: 20px;
        }

        /* ===== FOOTER ===== */
        .footer { margin-top: auto; padding: 20px 0; text-align: center; }
        .footer-links { display: flex; justify-content: center; gap: 20px; margin-bottom: 10px; }
        .footer-links a { color: #64748b; font-size: 12px; text-decoration: none; transition: 0.3s; }
        .footer-links a:hover { color: var(--primary); }
        .copyright { font-size: 9px; color: #475569; text-transform: uppercase; letter-spacing: 1px; }

    </style>
</head>
<body>
    <div class="bg-glow"></div>
    <div class="grid-bg"></div>

    <div class="app-container">
        <!-- Header -->
        <header class="header">
            <div class="logo-wrapper">
                <i class="fa-solid fa-bolt-lightning"></i>
            </div>
            <h1 class="title">WAHM CLOUD</h1>
            <p class="subtitle">Advanced Injection Infrastructure</p>
        </header>

        <!-- User Card -->
        <div class="user-card">
            <div class="avatar-box" id="avatarBox">
                <img id="userImg" src="" style="display:none;">
                <i class="fa-solid fa-user-secret" id="userPlaceholder"></i>
            </div>
            <div class="user-meta">
                <div class="user-name" id="userName">Loading Profile...</div>
                <div class="user-id" id="userId">ID: 0000000000</div>
                <div id="userBadge" class="badge">Checking...</div>
            </div>
            <div class="stats-box">
                <div class="stats-val" id="attemptsVal">--</div>
                <div class="stats-label">Attempts</div>
            </div>
        </div>

        <!-- Form Section -->
        <div class="form-section">
            <form id="mainForm">
                <div class="input-group">
                    <label class="label">Telegram Bot Token</label>
                    <div class="input-wrapper">
                        <input type="password" id="tokenInput" class="input-field" placeholder="Paste your token here..." required>
                        <i class="fa-solid fa-key"></i>
                    </div>
                </div>
                
                <button type="submit" class="submit-btn">
                    <i class="fa-solid fa-wand-magic-sparkles"></i>
                    <span>START INJECTION</span>
                </button>
            </form>

            <!-- Progress Overlay -->
            <div class="progress-overlay" id="progressOverlay">
                <div class="loader-ring"></div>
                <div class="progress-text" id="statusText">Initializing...</div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" id="progressBar"></div>
                </div>
                <div class="text-[10px] text-slate-500 mt-4 uppercase tracking-widest" id="percentText">0% COMPLETE</div>
            </div>

            <!-- Success View -->
            <div class="success-view" id="successView">
                <div class="check-icon"><i class="fa-solid fa-check"></i></div>
                <h2 class="text-xl font-black mb-2">SUCCESSFUL!</h2>
                <p class="text-xs text-slate-400">Your application has been signed and injected successfully.</p>
                <a href="#" id="downloadLink" class="download-btn">
                    <i class="fa-solid fa-download"></i>
                    DOWNLOAD APK
                </a>
                <button onclick="location.reload()" class="block mx-auto mt-6 text-[10px] text-slate-500 uppercase font-bold tracking-widest hover:text-white transition">New Injection</button>
            </div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            <div class="footer-links">
                <a href="#">Privacy</a>
                <a href="#">Terms</a>
                <a href="#">API Docs</a>
                <a href="#">Support</a>
            </div>
            <div class="copyright">© 2024 WAHM ENTERPRISE. ALL RIGHTS RESERVED.</div>
        </footer>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        tg.headerColor = '#020617';
        tg.backgroundColor = '#020617';

        const user = tg.initDataUnsafe.user || { id: 8349168441, first_name: 'Anonymous User' };
        
        // Init UI
        document.getElementById('userName').innerText = user.first_name + (user.last_name ? ' ' + user.last_name : '');
        document.getElementById('userId').innerText = 'ID: ' + user.id;
        if(user.photo_url) {
            document.getElementById('userImg').src = user.photo_url;
            document.getElementById('userImg').style.display = 'block';
            document.getElementById('userPlaceholder').style.display = 'none';
        }

        async function refreshUserData() {
            try {
                const res = await fetch('/api/user/' + user.id);
                const data = await res.json();
                
                const badge = document.getElementById('userBadge');
                if(data.is_vip) {
                    badge.innerText = 'VIP MEMBER';
                    badge.className = 'badge badge-vip';
                    document.getElementById('attemptsVal').innerText = '∞';
                } else {
                    badge.innerText = 'FREE TRIAL';
                    badge.className = 'badge badge-free';
                    document.getElementById('attemptsVal').innerText = data.attempts;
                }
            } catch(e) {}
        }
        refreshUserData();

        document.getElementById('mainForm').onsubmit = async (e) => {
            e.preventDefault();
            const token = document.getElementById('tokenInput').value;
            if(!token) return;

            const overlay = document.getElementById('progressOverlay');
            const status = document.getElementById('statusText');
            const bar = document.getElementById('progressBar');
            const percent = document.getElementById('percentText');
            
            overlay.style.display = 'flex';
            
            const steps = [
                { p: 20, t: 'Connecting to Cloud...' },
                { p: 45, t: 'Decrypting Package...' },
                { p: 70, t: 'Injecting Token...' },
                { p: 90, t: 'Finalizing Sign...' },
                { p: 99, t: 'Packaging APK...' }
            ];

            let currentP = 0;
            let stepIdx = 0;
            const timer = setInterval(() => {
                if(stepIdx < steps.length) {
                    if(currentP < steps[stepIdx].p) {
                        currentP += Math.random() * 2;
                        bar.style.width = currentP + '%';
                        percent.innerText = Math.floor(currentP) + '% COMPLETE';
                        status.innerText = steps[stepIdx].t;
                    } else {
                        stepIdx++;
                    }
                }
            }, 100);

            const formData = new FormData();
            formData.append('token', token);
            formData.append('user_id', user.id);

            try {
                const response = await fetch('/generate', { method: 'POST', body: formData });
                clearInterval(timer);
                
                if(response.ok) {
                    bar.style.width = '100%';
                    percent.innerText = '100% COMPLETE';
                    status.innerText = 'Success!';
                    
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    
                    setTimeout(() => {
                        overlay.style.display = 'none';
                        document.getElementById('mainForm').style.display = 'none';
                        document.getElementById('successView').style.display = 'block';
                        document.getElementById('downloadLink').href = url;
                        document.getElementById('downloadLink').download = 'wahm_g5wbot.apk';
                    }, 800);
                } else {
                    alert('Injection Failed. Please check your token or attempts.');
                    location.reload();
                }
            } catch(e) {
                alert('Connection Error');
                location.reload();
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
    
    if not user_data['is_vip'] and user_data['attempts'] <= 0:
        return "Limit reached", 403
        
    if not os.path.exists(BASE_APK):
        return "Base file missing", 500
        
    output = os.path.join(UPLOAD_FOLDER, f'mod_{user_id}.apk')
    os.system(f"cp {BASE_APK} {output}")
    
    if not user_data['is_vip']:
        user_data['attempts'] -= 1
        db.save_users()
        
    return send_file(output, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

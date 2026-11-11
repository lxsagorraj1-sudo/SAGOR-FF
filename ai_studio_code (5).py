import os
import sys
import time
import json
import secrets
import threading
from functools import wraps
from flask import Flask, request, jsonify, session

# psutil সেফ ইমপোর্ট (না থাকলেও ক্র্যাশ করবে না)
try:
    import psutil
except ImportError:
    psutil = None

app = Flask(__name__)

# ডাটা ডিরেক্টরি সেটআপ
DATA_DIR = os.environ.get("SAGOR_DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "db.json")
SECRET_FILE = os.path.join(DATA_DIR, ".secret_key")

# সেশন সিক্রেট কি স্থায়ী করা (যাতে বারবার লগআউট না হয়)
if not os.path.exists(SECRET_FILE):
    with open(SECRET_FILE, "w", encoding="utf-8") as f:
        f.write(secrets.token_hex(32))
with open(SECRET_FILE, "r", encoding="utf-8") as f:
    app.secret_key = os.environ.get("SESSION_SECRET", f.read().strip())

# ডাটাবেজ ফাইল যেন একই সাথে ক্র্যাশ না করে সেজন্য থ্রেড লক
db_lock = threading.Lock()

# ----------------- ডিফল্ট ডাটাবেজ স্ট্রাকচার -----------------
def get_default_db():
    return {
        "owner": {"password": "admin"},
        "users": {},
        "keys": [],
        "settings": {
            "bot": {"online": True, "enabled": True, "uptime": 360, "insquad": False, "auto_match": True, "uid": "611211106"},
            "ident": {"uid": "611211106", "name": "SAGOR-BOT", "region": "BD", "clan_id": "88888", "online": "Online-BD", "chat": "Chat-BD"},
            "features": {"Auto Emote": True, "Auto Leave": False, "Fast Squad": True, "Auto Invite": True, "Ghost Revenge": True},
            "ghost": {"enabled": True, "name": "SAGOR"},
            "min_level": 10,
            "ai": {"on": True, "mood": "friendly", "moods": [{"key": "friendly", "label": "😊 Friendly"}, {"key": "toxic", "label": "😈 Aggressive"}, {"key": "pro", "label": "🔥 Pro Gamer"}]},
            "auto_friend": True,
            "sub_admins": ["611211106"],
            "blocked": [],
            "autolike": [{"uid": "11223344", "server": "BD"}],
            "locks": [],
            "seller_admins": ["611211106"],
            "links": {
                "apk": "https://mediafire.com",
                "wa_number": "https://wa.me/8801328498160",
                "wa_channel": "https://whatsapp.com/channel/example",
                "wa_group": "https://chat.whatsapp.com/example",
                "telegram": "https://t.me/example",
                "tg_bot": "https://t.me/botsagor_420",
                "tiktok": "https://tiktok.com/@example",
                "youtube": "https://youtube.com/@example",
                "website": "https://google.com",
                "guild": "https://google.com"
            },
            "notice": "🔥 SAGOR TCP BOT Panel এ স্বাগতম! কোনো সমস্যা হলে অ্যাডমিনের সাথে যোগাযোগ করুন।"
        },
        "extra_bots": [],
        "logs": []
    }

def load_db():
    with db_lock:
        if not os.path.exists(DB_FILE):
            default_data = get_default_db()
            save_db_internal(default_data)
            return default_data
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return get_default_db()
                return data
        except Exception:
            return get_default_db()

def save_db_internal(data):
    # সেফ রাইটিং যাতে হঠাৎ ক্র্যাশ করলেও আসল ফাইল নষ্ট না হয়
    tmp_file = DB_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_file, DB_FILE)

def save_db(data):
    with db_lock:
        try:
            save_db_internal(data)
        except Exception as e:
            print(f"[Error saving DB]: {e}")

def log_msg(msg):
    try:
        db = load_db()
        t_str = time.strftime("%H:%M:%S")
        db.setdefault("logs", []).append({"t": t_str, "m": str(msg)})
        if len(db["logs"]) > 500:
            db["logs"] = db["logs"][-500:]
        save_db(db)
    except Exception:
        pass

def get_system_metrics():
    cpu, ram, disk = 0, 0, 0
    if psutil:
        try:
            cpu = psutil.cpu_percent(interval=None)
        except Exception:
            cpu = 0
        try:
            ram = psutil.virtual_memory().percent
        except Exception:
            ram = 0
        try:
            path = "C:\\" if os.name == "nt" else "/"
            disk = psutil.disk_usage(path).percent
        except Exception:
            disk = 0
    return {"cpu": cpu, "ram": ram, "disk": disk}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "role" not in session:
            return jsonify({"ok": False, "error": "login required"}), 401
        return f(*args, **kwargs)
    return decorated

# ----------------- ফ্রন্টএন্ড UI (HTML/CSS/JS) -----------------
HTML_CONTENT = """<!DOCTYPE html>
<html lang="bn">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
    <title>SAGOR Control Panel</title>
    <meta name="theme-color" content="#05050d" />
    <style>
      :root{--bg:#05050d;--card:#0a0a17;--tile:#06060f;--bd:#1a1a32;--tx:#eef0ff;--t2:#8b8fb3;--gold:#f7c948;--blue:#3ea6ff;--cyan:#19d3ff;--pur:#9b5cff;--red:#ff3b5c;--ok:#35e08a;--lab:#e9c46a}
      *{box-sizing:border-box}
      body{margin:0;background:radial-gradient(900px 420px at 50% -80px,#15102e,transparent),var(--bg);color:var(--tx);font:15px/1.4 "Inter",system-ui,-apple-system,sans-serif;padding-bottom:96px}
      button,input,select,textarea{font:inherit;color:inherit}
      .hide{display:none!important}
      #login{max-width:340px;margin:14vh auto;padding:24px;background:var(--card);border:1px solid var(--bd);border-radius:16px;text-align:center;box-shadow:0 0 50px rgba(155,92,255,.15)}
      #login h2{margin:6px 0 2px;font-size:26px;background:linear-gradient(90deg,#c83cd2,#ff3b6b);-webkit-background-clip:text;background-clip:text;color:transparent}
      #login .sub{color:var(--t2);font-size:13px;margin-bottom:16px}
      .fi{position:relative;margin-bottom:10px}.fi span{position:absolute;left:13px;top:50%;transform:translateY(-50%);opacity:.55}.fi input{padding-left:40px;height:44px;border-radius:12px;background:#04040a}
      .btn.lg{width:100%;height:44px;border-radius:12px;color:#10101c;background:linear-gradient(90deg,#f2c14e,#8a4dff 60%,#3e8bff);font-weight:700;border:0;cursor:pointer}
      input,select,textarea{width:100%;background:var(--tile);border:1px solid var(--bd);border-radius:10px;padding:9px 11px;outline:none}
      input:focus,textarea:focus,select:focus{border-color:var(--blue)}
      .btn{background:linear-gradient(90deg,#ff2bd6,#7a3cff);border:0;border-radius:10px;padding:9px 14px;font-weight:700;cursor:pointer;white-space:nowrap;color:#fff}
      .btn.alt{background:var(--tile);border:1px solid var(--bd)}.btn.bad{background:var(--red)}
      .wrap{max-width:1000px;margin:auto;padding:12px}
      .hero{position:relative;overflow:hidden;border:1px solid var(--bd);border-radius:20px;min-height:120px;display:flex;align-items:center;padding:18px;background:linear-gradient(90deg,rgba(5,5,13,.97) 28%,rgba(5,5,13,.55) 62%,rgba(5,5,13,.15)),#07070f}
      .hero h1{margin:0;font-size:24px;background:linear-gradient(90deg,var(--gold),#ff7a59 55%,var(--blue));-webkit-background-clip:text;background-clip:text;color:transparent}
      .hero small{display:block;margin-top:4px;letter-spacing:2px;font-size:11px;color:var(--t2)}
      .hbar{position:absolute;top:12px;right:12px;display:flex;gap:6px;align-items:center}
      .pill{display:inline-flex;align-items:center;gap:6px;background:rgba(10,10,23,.85);border:1px solid var(--bd);border-radius:14px;padding:4px 10px;font-size:11px;color:var(--t2)}
      .pill.gold{color:var(--gold);border-color:#4a3d12}.pill.red{background:#c8203e;border-color:#c8203e;color:#fff;cursor:pointer}
      .dot{width:8px;height:8px;border-radius:50%;background:var(--red);display:inline-block}.dot.on{background:var(--ok);box-shadow:0 0 8px var(--ok)}
      .card{background:var(--card);border:1px solid var(--bd);border-radius:16px;padding:14px;margin-top:12px}
      .card h3{margin:0 0 12px;font-size:14px;color:var(--blue);display:flex;align-items:center;gap:8px}
      .card h3.g{color:var(--gold);text-transform:uppercase}
      .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px}
      .tile{background:var(--tile);border:1px solid #11112a;border-radius:12px;padding:12px 8px;text-align:center}
      .tile small{display:block;font-size:10px;letter-spacing:1px;color:var(--lab);margin-bottom:4px;font-weight:700}
      .tile b{display:block;font-size:16px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .tile b.ok{color:var(--ok)}
      .tools{display:flex;gap:6px;align-items:center;margin-bottom:8px}
      .tools .btn{padding:6px 12px;font-size:12px}
      #logs{height:300px;overflow-y:auto;background:#04040b;border:1px solid #11112a;border-radius:12px;padding:8px 10px;font:12px/1.6 monospace}
      #logs div{border-left:3px solid var(--gold);padding-left:8px;margin-bottom:4px;color:#cfd3f5}
      #logs .t{color:#6f739a;margin-right:6px}
      .row{display:flex;gap:8px;align-items:center;margin-bottom:8px}
      .tg{display:flex;justify-content:space-between;align-items:center;background:var(--tile);border:1px solid #11112a;border-radius:12px;padding:10px 14px;cursor:pointer}
      .sw{width:36px;height:20px;border-radius:10px;background:#2c2c4d;position:relative;transition:.2s}
      .sw::after{content:"";position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;background:#fff;transition:.2s}
      .tg.on .sw{background:var(--ok)}.tg.on .sw::after{left:18px}
      .chip{display:inline-flex;gap:6px;align-items:center;background:var(--tile);border:1px solid var(--bd);border-radius:16px;padding:4px 10px;margin:4px;font-size:12px;cursor:pointer}
      #toast{position:fixed;left:50%;bottom:30px;transform:translateX(-50%);background:var(--card);border:1px solid var(--blue);padding:9px 16px;border-radius:12px;opacity:0;pointer-events:none;transition:.2s;z-index:999}
      #toast.show{opacity:1}#toast.err{border-color:var(--red)}
    </style>
  </head>
  <body>
    <!-- LOGIN / REGISTER -->
    <div id="login" class="hide">
      <div id="lgBox">
        <h2>Welcome Back</h2>
        <div class="sub">SAGOR Bot Control Panel</div>
        <div class="fi"><span>👤</span><input id="lu" placeholder="Username (Owner হলে ফাঁকা রাখুন)" autocomplete="username" /></div>
        <div class="fi"><span>🔒</span><input id="pw" type="password" placeholder="Password (default: admin)" autocomplete="current-password" /></div>
        <button class="btn lg" id="loginBtn">⇥ Login</button>
        <div style="margin-top:14px;padding-top:10px;border-top:1px solid #11112a;font-size:13px">
          <a data-view="rgBox" style="color:#ffe08a;cursor:pointer">＋ Create Account with Key</a>
        </div>
      </div>
      <div id="rgBox" class="hide">
        <h2>Register</h2>
        <div class="sub">রেজিস্ট্রেশন করতে কী (Key) দিন</div>
        <div class="fi"><span>👤</span><input id="ru" placeholder="Username" /></div>
        <div class="fi"><span>🔒</span><input id="rp" type="password" placeholder="Password (min 6 chars)" /></div>
        <div class="fi"><span>🔑</span><input id="rk" placeholder="SAGOR Key" /></div>
        <button class="btn lg" id="rgBtn">✈ Register</button>
        <div style="margin-top:14px"><a data-view="lgBox" style="color:#ffe08a;cursor:pointer">← Back to Login</a></div>
      </div>
    </div>

    <!-- OWNER DASHBOARD -->
    <div id="app" class="hide">
      <div class="wrap">
        <div class="hero">
          <div class="hbar">
            <span class="pill"><i class="dot" id="cDot"></i><span id="cTx">Connecting...</span></span>
            <span class="pill gold">OWNER</span>
            <button class="pill red" id="logout">Logout</button>
          </div>
          <div>
            <h1>SAGOR PREMIUM</h1>
            <small>ELITE BOT CONTROLLER</small>
          </div>
        </div>
        <div class="card">
          <h3>🤖 Bot Identity & Status</h3>
          <div class="grid" id="ident"></div>
        </div>
        <div class="card">
          <h3 class="c">📈 System Performance</h3>
          <div class="grid" id="perf"></div>
        </div>
        <div class="card">
          <div class="tools">
            <button class="btn" id="bClear">Clear Logs</button>
            <span style="margin-left:auto;font-size:11px;color:var(--t2)">Auto-refreshing</span>
          </div>
          <div id="logs"></div>
        </div>
        <div class="card">
          <h3 class="g">Control Center</h3>
          <div id="sw1" style="margin-bottom:10px"></div>
          <div class="row">
            <button class="btn bad" id="restartBtn">Restart Bot</button>
          </div>
        </div>
        <div class="card">
          <h3 class="g">💰 Key & User Management</h3>
          <div class="row">
            <input id="kDays" type="number" min="1" max="365" placeholder="কত দিন (उदा: 30)" />
            <input id="kCnt" type="number" min="1" max="50" placeholder="কয়টি" style="max-width:80px" />
            <button class="btn" id="kGen">Generate Key</button>
          </div>
          <textarea id="kOut" readonly placeholder="জেনারেট হওয়া Key এখানে দেখা যাবে..." style="min-height:50px"></textarea>
          <div style="margin:8px 0 4px;font-size:12px;color:var(--t2)">Generated Keys (ক্লিক করে কপি করুন):</div>
          <div id="kList"></div>
          <div style="margin:8px 0 4px;font-size:12px;color:var(--t2)">Registered Users:</div>
          <div id="uList"></div>
        </div>
      </div>
    </div>

    <!-- USER DASHBOARD -->
    <div id="uapp" class="hide">
      <div class="wrap">
        <div class="hero">
          <div class="hbar">
            <span class="pill gold" id="uName">User</span>
            <button class="pill red" id="uLogout">Logout</button>
          </div>
          <div>
            <h1>SAGOR PREMIUM</h1>
            <small>USER DASHBOARD</small>
          </div>
        </div>
        <div class="card" id="uNotice" style="color:var(--gold)"></div>
        <div class="card">
          <h3 class="g">⏱ Subscription Details</h3>
          <div class="grid" id="uSub"></div>
        </div>
        <div class="card">
          <h3>🤖 Bot Status</h3>
          <div class="grid" id="uTiles"></div>
        </div>
      </div>
    </div>

    <div id="toast"></div>

    <script>
      const $=s=>document.querySelector(s);
      let poll=null,logPoll=null;
      const esc=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
      
      function toast(m,err){
        const t=$('#toast');t.textContent=m;t.className='show'+(err?' err':'');
        setTimeout(()=>t.className='',2500);
      }
      
      async function api(path,body){
        const o=body===undefined?{credentials:'same-origin'}:{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};
        try{
          const r=await fetch(path,o);
          if(r.status===401&&path!=='/api/login'&&path!=='/api/register'){showLogin();return {ok:false};}
          return await r.json();
        }catch(e){
          return {ok:false,error:'Server unreachable'};
        }
      }

      function showLogin(){
        clearInterval(poll);clearInterval(logPoll);
        $('#app').classList.add('hide');$('#uapp').classList.add('hide');$('#login').classList.remove('hide');
      }
      function showApp(){
        $('#login').classList.add('hide');$('#uapp').classList.add('hide');$('#app').classList.remove('hide');
        refresh();loadSales();pullLogs();
        clearInterval(poll);clearInterval(logPoll);
        poll=setInterval(refresh,4000);logPoll=setInterval(pullLogs,2500);
      }
      function showUser(){
        $('#login').classList.add('hide');$('#app').classList.add('hide');$('#uapp').classList.remove('hide');
        uRefresh();
        clearInterval(poll);
        poll=setInterval(uRefresh,5000);
      }

      async function pullLogs(){
        const j=await api('/api/logs');
        if(!j||!j.ok||!j.logs)return;
        const L=$('#logs');
        L.innerHTML=j.logs.slice(-60).map(r=>`<div><span class="t">${esc(r.t)}</span>${esc(r.m)}</div>`).join('');
        L.scrollTop=L.scrollHeight;
      }

      async function refresh(){
        const j=await api('/api/status');
        if(!j||!j.ok)return;
        $('#cDot').className='dot '+(j.bot&&j.bot.online?'on':'');
        $('#cTx').textContent=j.bot&&j.bot.online?'Bot Online':'Bot Offline';
        $('#ident').innerHTML=`
          <div class="tile"><small>UID</small><b>${esc(j.ident&&j.ident.uid||'N/A')}</b></div>
          <div class="tile"><small>NAME</small><b>${esc(j.ident&&j.ident.name||'SAGOR')}</b></div>
          <div class="tile"><small>STATUS</small><b class="ok">${j.bot&&j.bot.online?'ONLINE':'OFFLINE'}</b></div>
        `;
        $('#perf').innerHTML=`
          <div class="tile"><small>CPU</small><b>${j.sys?j.sys.cpu:0}%</b></div>
          <div class="tile"><small>RAM</small><b>${j.sys?j.sys.ram:0}%</b></div>
          <div class="tile"><small>DISK</small><b>${j.sys?j.sys.disk:0}%</b></div>
        `;
        const en=j.bot&&j.bot.enabled;
        $('#sw1').innerHTML=`<div class="tg ${en?'on':''}" onclick="setBot(${!en})"><span>Bot Engine Active</span><i class="sw"></i></div>`;
      }

      async function setBot(v){
        await api('/api/set',{kind:'bot',value:v});
        refresh();
      }

      async function loadSales(){
        const j=await api('/api/sales');
        if(!j||!j.ok)return;
        $('#kList').innerHTML=(j.keys||[]).map(k=>`<span class="chip" onclick="navigator.clipboard.writeText('${k.key}');toast('Key Copied!')">🔑 ${esc(k.key)} (${k.days}d) ${k.used_by?'(Used: '+esc(k.used_by)+')':'✅'}</span>`).join('')||'<span style="font-size:12px;color:var(--t2)">কোনো কি পাওয়া যায়নি</span>';
        $('#uList').innerHTML=(j.users||[]).map(u=>`<div class="tg" style="cursor:default;margin-bottom:6px"><span><b>${esc(u.name)}</b></span><span>${u.active?'🟢 Active':'🔴 Expired'}</span></div>`).join('')||'<span style="font-size:12px;color:var(--t2)">কোনো ইউজার নেই</span>';
      }

      $('#kGen').onclick=async()=>{
        const days=+$('#kDays').value||30,count=+$('#kCnt').value||1;
        const j=await api('/api/sales',{action:'genkeys',days,count});
        if(j&&j.ok){
          $('#kOut').value=(j.new_keys||[]).join('\\n');
          loadSales();
          toast('Key Generated ✔');
        }
      };

      async function uRefresh(){
        const j=await api('/api/me');
        if(!j||!j.ok)return;
        $('#uName').textContent=j.username||'User';
        $('#uNotice').textContent=j.notice||'';
        $('#uSub').innerHTML=`
          <div class="tile"><small>DAYS LEFT</small><b class="ok">${j.sub?j.sub.days:0} Days</b></div>
          <div class="tile"><small>EXPIRY</small><b>${j.sub?new Date(j.sub.expires*1000).toLocaleDateString():'N/A'}</b></div>
        `;
        $('#uTiles').innerHTML=`<div class="tile"><small>STATUS</small><b class="ok">🟢 RUNNING</b></div>`;
      }

      $('#loginBtn').onclick=async()=>{
        const u=$('#lu').value.trim(),p=$('#pw').value;
        const j=await api('/api/login',{username:u,password:p});
        if(j&&j.ok) boot();
        else toast(j.error||'লগইন ব্যর্থ হয়েছে',1);
      };

      $('#rgBtn').onclick=async()=>{
        const u=$('#ru').value.trim(),p=$('#rp').value,k=$('#rk').value.trim();
        const j=await api('/api/register',{username:u,password:p,key:k});
        if(j&&j.ok){toast('Account created ✔');boot();}
        else toast(j.error||'রেজিস্ট্রেশন ব্যর্থ হয়েছে',1);
      };

      $('#logout').onclick=$('#uLogout').onclick=async()=>{
        await api('/api/logout',{});
        showLogin();
      };

      $('#restartBtn').onclick=async()=>{
        await api('/api/restart',{});
        toast('Bot Restarted ✔');
      };

      $('#bClear').onclick=()=>{$('#logs').innerHTML=''};

      document.querySelectorAll('[data-view]').forEach(a=>a.onclick=()=>{
        $('#lgBox').classList.toggle('hide',a.dataset.view!=='lgBox');
        $('#rgBox').classList.toggle('hide',a.dataset.view!=='rgBox');
      });

      async function boot(){
        const j=await api('/api/me');
        if(j&&j.ok){
          if(j.role==='owner') showApp();
          else showUser();
        }else{
          showLogin();
        }
      }
      boot();
    </script>
  </body>
</html>
"""

# ----------------- ব্যাকএন্ড API রাউটস -----------------

@app.route("/")
def index():
    return HTML_CONTENT

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    u = str(data.get("username", "")).strip()
    p = str(data.get("password", ""))
    db = load_db()

    # Owner Login
    if not u or u.lower() == "owner":
        owner_pass = db.get("owner", {}).get("password", "admin")
        if p == owner_pass:
            session["role"] = "owner"
            session["user"] = "Owner"
            log_msg("👑 [OWNER] Owner সফলভাবে লগইন করেছেন")
            return jsonify({"ok": True, "role": "owner"})
        return jsonify({"ok": False, "error": "ভুল পাসওয়ার্ড! (Default: admin)"}), 400

    # User Login
    users = db.get("users", {})
    user = users.get(u)
    if not user or user.get("password") != p:
        return jsonify({"ok": False, "error": "ভুল Username বা Password"}), 400

    session["role"] = "user"
    session["user"] = u
    log_msg(f"👤 [USER] '{u}' লগইন করেছেন")
    return jsonify({"ok": True, "role": "user"})

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    u = str(data.get("username", "")).strip()
    p = str(data.get("password", ""))
    k = str(data.get("key", "")).strip()

    if not u or len(p) < 6:
        return jsonify({"ok": False, "error": "পাসওয়ার্ড কমপক্ষে ৬ অক্ষরের হতে হবে"}), 400

    db = load_db()
    users = db.setdefault("users", {})
    if u in users:
        return jsonify({"ok": False, "error": "এই Username টি ইতিমধ্যে ব্যবহৃত হচ্ছে"}), 400

    keys = db.setdefault("keys", [])
    key_obj = next((item for item in keys if item.get("key") == k and not item.get("used_by")), None)
    if not key_obj:
        return jsonify({"ok": False, "error": "ভুল বা পূর্বে ব্যবহৃত Key"}), 400

    now = int(time.time())
    days = int(key_obj.get("days", 30))
    key_obj["used_by"] = u

    users[u] = {
        "password": p,
        "key": k,
        "expires": now + (days * 86400),
        "disabled": False,
        "bot": {"uid": "11223344", "running": True}
    }
    save_db(db)
    session["role"] = "user"
    session["user"] = u
    log_msg(f"✅ [REGISTER] নতুন ইউজার '{u}' সফলভাবে যুক্ত হয়েছে (Key: {k})")
    return jsonify({"ok": True})

@app.route("/api/me")
@login_required
def api_me():
    db = load_db()
    if session.get("role") == "owner":
        return jsonify({"ok": True, "role": "owner", "username": "Owner"})

    u = session.get("user")
    user = db.get("users", {}).get(u)
    if not user:
        session.clear()
        return jsonify({"ok": False, "error": "User not found"}), 401

    now = int(time.time())
    expires = user.get("expires", now)
    left_sec = max(0, expires - now)
    return jsonify({
        "ok": True,
        "role": "user",
        "username": u,
        "notice": db.get("settings", {}).get("notice", ""),
        "sub": {
            "active": left_sec > 0 and not user.get("disabled", False),
            "days": left_sec // 86400,
            "expires": expires
        },
        "bot": user.get("bot", {})
    })

@app.route("/api/status")
@login_required
def api_status():
    db = load_db()
    st = db.get("settings", {})
    return jsonify({
        "ok": True,
        "bot": st.get("bot", {}),
        "ident": st.get("ident", {}),
        "ghost": st.get("ghost", {}),
        "features": st.get("features", {}),
        "sys": get_system_metrics()
    })

@app.route("/api/logs")
@login_required
def api_logs():
    db = load_db()
    return jsonify({"ok": True, "logs": db.get("logs", [])})

@app.route("/api/set", methods=["POST"])
@login_required
def api_set():
    data = request.json or {}
    db = load_db()
    if data.get("kind") == "bot":
        val = bool(data.get("value", True))
        db.setdefault("settings", {}).setdefault("bot", {})["enabled"] = val
        log_msg(f"⚙ [CONFIG] Bot enabled অবস্থা পরিবর্তিত হয়েছে: {val}")
    save_db(db)
    return jsonify({"ok": True})

@app.route("/api/sales", methods=["GET", "POST"])
@login_required
def api_sales():
    if session.get("role") != "owner":
        return jsonify({"ok": False, "error": "Access Denied"}), 403

    db = load_db()
    if request.method == "POST":
        data = request.json or {}
        if data.get("action") == "genkeys":
            days = int(data.get("days", 30))
            count = min(int(data.get("count", 1)), 50)
            new_keys = []
            keys_list = db.setdefault("keys", [])
            for _ in range(count):
                k = f"SAGOR-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
                keys_list.append({"key": k, "days": days, "used_by": None})
                new_keys.append(k)
            save_db(db)
            log_msg(f"🔑 [KEYS] নতুন {count} টি Key জেনারেট করা হয়েছে ({days} দিনের)")
            return jsonify({"ok": True, "new_keys": new_keys, "keys": keys_list})

    now = int(time.time())
    users_list = [
        {"name": name, "active": u.get("expires", 0) > now}
        for name, u in db.get("users", {}).items()
    ]
    return jsonify({"ok": True, "keys": db.get("keys", []), "users": users_list})

@app.route("/api/restart", methods=["POST"])
@login_required
def api_restart():
    log_msg("🔄 [RESTART] Bot সফলভাবে রিস্টার্ট দেওয়া হয়েছে")
    return jsonify({"ok": True})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})

# ----------------- সার্ভার রান -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 SAGOR Panel চালু হয়েছে: http://localhost:{port}")
    # threaded=True দিয়ে নির্বিঘ্ন ব্যাকগ্রাউন্ড সাপোর্ট নিশ্চিত করা হলো
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
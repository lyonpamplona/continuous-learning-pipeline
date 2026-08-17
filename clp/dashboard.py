"""Dashboard module — generates web dashboard for skill review."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from clp.scorer import Scorer


class Dashboard:
    """Generates web dashboard for skill review."""

    def __init__(self, config=None):
        self.config = config or {}
        self.scorer = Scorer()
        self.reports_dir = Path(self.config.get("reports_dir", "~/.clp/reports")).expanduser()
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, pending_dir: str = None, approved_dir: str = None,
                 rejected_dir: str = None, generate_html: bool = True) -> dict:
        """Generate dashboard with current skill status."""
        workspace = Path(self.config.get("workspace_dir", "~/.clp/workspace")).expanduser()

        if pending_dir is None:
            pending_dir = workspace / "pending"
        if approved_dir is None:
            approved_dir = workspace / "approved"
        if rejected_dir is None:
            rejected_dir = workspace / "rejected"

        pending_dir = Path(pending_dir)
        approved_dir = Path(approved_dir)
        rejected_dir = Path(rejected_dir)

        # Collect pending skills
        pending_skills = []
        if pending_dir.exists():
            for skill_dir in pending_dir.iterdir():
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        skill_data = self.scorer.load_skill(str(skill_file))
                        if skill_data:
                            score_result = self.scorer.score(skill_data)
                            pending_skills.append({
                                "name": skill_data["frontmatter"].get("name", "unknown"),
                                "description": skill_data["frontmatter"].get("description", ""),
                                "score": score_result["score"],
                                "decision": score_result["decision"],
                                "checks": score_result["checks"],
                                "size": len(skill_data["content"]),
                                "path": str(skill_file),
                            })

        # Count approved and rejected
        approved_count = len(list(approved_dir.iterdir())) if approved_dir.exists() else 0
        rejected_count = len(list(rejected_dir.iterdir())) if rejected_dir.exists() else 0

        result = {
            "pending": len(pending_skills),
            "approved": approved_count,
            "rejected": rejected_count,
            "skills": pending_skills,
        }

        # Generate HTML dashboard
        if generate_html:
            html_path = self.reports_dir / "review-dashboard.html"
            html = self._generate_html(pending_skills, approved_count, rejected_count)
            html_path.write_text(html)
            result["html_path"] = str(html_path)

        # Generate Markdown dashboard
        md_path = self.reports_dir / "review-dashboard.md"
        md = self._generate_markdown(pending_skills, approved_count, rejected_count)
        md_path.write_text(md)
        result["md_path"] = str(md_path)

        return result

    def _generate_html(self, pending_skills, approved_count, rejected_count) -> str:
        """Generate HTML dashboard with CLI/IDE aesthetic."""
        skills_json = json.dumps(pending_skills, ensure_ascii=False)

        html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>skill-review // clp</title>
<style>
:root{
--bg:#0a0e14;--bg2:#0d1117;--bg3:#161b22;--bg4:#1c2128;
--border:#21262d;--border2:#30363d;--focus:#58a6ff;
--text:#e6edf3;--text2:#8b949e;--text3:#484f58;--muted:#30363d;
--pass:#3fb950;--pass-bg:rgba(63,185,80,.1);
--fail:#f85149;--fail-bg:rgba(248,81,73,.1);
--warn:#d29922;--warn-bg:rgba(210,153,34,.1);
--info:#58a6ff;--info-bg:rgba(88,166,255,.1);
--mono:'JetBrains Mono','Fira Code','SF Mono','Cascadia Code','Consolas',monospace;
--r:3px;--max:720px;
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html{font-size:14px;-webkit-text-size-adjust:100%}
body{font-family:var(--mono);background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh;overflow-x:hidden;-webkit-font-smoothing:antialiased}
.shell{max-width:var(--max);margin:0 auto;padding:12px;min-height:100vh}
.header{display:flex;align-items:center;justify-content:space-between;padding:8px 16px;background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);margin-bottom:12px;position:relative;overflow:hidden}
.header::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--border2),transparent)}
.header-left{display:flex;align-items:center;gap:8px}
.dots{display:flex;gap:2px}
.dot{width:10px;height:10px;border-radius:50%;background:var(--border)}
.dot:nth-child(1){background:#f85149}.dot:nth-child(2){background:#d29922}.dot:nth-child(3){background:#3fb950}
.hdr-title{font-size:12px;color:var(--text2);letter-spacing:.5px}
.hdr-title .p{color:var(--text3)}
.hdr-time{font-size:11px;color:var(--text3);font-variant-numeric:tabular-nums}
.sbar{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}
.scell{background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);padding:16px;position:relative;overflow:hidden}
.scell::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px}
.scell.p::after{background:var(--warn)}.scell.a::after{background:var(--pass)}.scell.r::after{background:var(--fail)}
.slabel{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--text3);margin-bottom:4px}
.sval{font-size:28px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1}
.scell.p .sval{color:var(--warn)}.scell.a .sval{color:var(--pass)}.scell.r .sval{color:var(--fail)}
.shdr{display:flex;align-items:center;justify-content:space-between;padding:8px 0;margin-bottom:8px;border-bottom:1px solid var(--border)}
.stitle{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--text2)}
.scount{font-size:11px;color:var(--text3);background:var(--bg3);padding:2px 8px;border-radius:var(--r);font-variant-numeric:tabular-nums}
.slist{display:flex;flex-direction:column;gap:8px}
.scard{background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);overflow:hidden;transition:border-color .15s ease}
.scard:hover{border-color:var(--border2)}
.scard-h{display:flex;align-items:center;gap:8px;padding:12px;border-bottom:1px solid var(--border)}
.sidx{font-size:11px;color:var(--text3);font-variant-numeric:tabular-nums;min-width:24px;text-align:right}
.sname{font-size:14px;font-weight:600;color:var(--text);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sscore{font-size:13px;font-weight:700;font-variant-numeric:tabular-nums;padding:2px 10px;border-radius:var(--r);letter-spacing:.5px}
.sscore.p{color:var(--pass);background:var(--pass-bg);border:1px solid rgba(63,185,80,.2)}
.sscore.f{color:var(--fail);background:var(--fail-bg);border:1px solid rgba(248,81,73,.2)}
.sscore.w{color:var(--warn);background:var(--warn-bg);border:1px solid rgba(210,153,34,.2)}
.scard-b{padding:12px}
.sdesc{font-size:12px;color:var(--text2);margin-bottom:8px;line-height:1.6}
.smeta{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:8px}
.smeta-i{font-size:11px;color:var(--text3)}.smeta-i span{color:var(--text2)}
.ctoggle{display:flex;align-items:center;gap:4px;padding:4px 8px;background:var(--bg3);border:1px solid var(--border);border-radius:var(--r);cursor:pointer;font-family:var(--mono);font-size:11px;color:var(--text3);width:100%;text-align:left;transition:all .15s ease;user-select:none;-webkit-user-select:none;-webkit-tap-highlight-color:transparent}
.ctoggle:hover{background:var(--bg4);color:var(--text2)}
.ctoggle .arr{transition:transform .2s ease;font-size:10px}
.ctoggle.exp .arr{transform:rotate(90deg)}
.clist{display:none;padding:8px;background:var(--bg);border:1px solid var(--border);border-top:none;border-radius:0 0 var(--r) var(--r);margin-top:-1px}
.clist.vis{display:block}
.citem{display:flex;align-items:flex-start;gap:4px;padding:2px 0;font-size:11px;line-height:1.5}
.cicon{min-width:14px;text-align:center;margin-top:1px}
.cicon.p{color:var(--pass)}.cicon.f{color:var(--fail)}.cicon.i{color:var(--text3)}
.ctext{color:var(--text2)}.ctext.f{color:var(--fail)}
.empty{text-align:center;padding:32px 16px;color:var(--text3)}
.empty .prompt{font-size:12px;margin-bottom:8px}
.empty .cur{display:inline-block;width:8px;height:16px;background:var(--info);animation:blink 1s step-end infinite;vertical-align:text-bottom}
@keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}
.footer{margin-top:24px;padding-top:12px;border-top:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.fl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px}
.fr{font-size:10px;color:var(--muted);font-variant-numeric:tabular-nums}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}::-webkit-scrollbar-thumb:hover{background:var(--border2)}
@keyframes fi{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
.scard{animation:fi .2s ease forwards}
.scard:nth-child(1){animation-delay:.05s}.scard:nth-child(2){animation-delay:.1s}.scard:nth-child(3){animation-delay:.15s}.scard:nth-child(4){animation-delay:.2s}.scard:nth-child(5){animation-delay:.25s}
.ld{display:flex;align-items:center;justify-content:center;padding:32px;color:var(--text3);font-size:12px}
.ld::before{content:'';width:12px;height:12px;border:1px solid var(--border);border-top-color:var(--info);border-radius:50%;animation:spin .8s linear infinite;margin-right:8px}
@keyframes spin{to{transform:rotate(360deg)}}
@media(max-width:480px){.shell{padding:8px}.sbar{gap:4px}.scell{padding:12px}.sval{font-size:22px}.scard-h{padding:8px}.scard-b{padding:8px}.smeta{flex-direction:column;gap:4px}}
</style>
</head>
<body>
<div class="shell" id="app">
<div class="header">
<div class="header-left">
<div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
<div class="hdr-title"><span class="p">~/.clp/workspace</span><span style="color:var(--text3)">/</span><span style="color:var(--text)">review-dashboard</span></div>
</div>
<div class="hdr-time" id="hdr-time"></div>
</div>
<div class="sbar">
<div class="scell p"><div class="slabel">pending</div><div class="sval" id="c-p">0</div></div>
<div class="scell a"><div class="slabel">approved</div><div class="sval" id="c-a">0</div></div>
<div class="scell r"><div class="slabel">rejected</div><div class="sval" id="c-r">0</div></div>
</div>
<div class="shdr">
<div class="stitle">pending skills</div>
<div class="scount" id="s-count">0 items</div>
</div>
<div class="slist" id="s-list"><div class="ld">loading...</div></div>
<div class="footer">
<div class="fl">clp // continuous learning pipeline</div>
<div class="fr" id="f-time"></div>
</div>
</div>
<script>
var SKILLS=PLACEHOLDER_SKILLS;
var D={
data:null,
init:function(){this.tick();setInterval(function(){D.tick()},1000);this.render()},
tick:function(){var n=new Date();var t=n.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});var d=n.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit',year:'numeric'});var h=document.getElementById('hdr-time');var f=document.getElementById('f-time');if(h)h.textContent=t;if(f)f.textContent=d+' '+t}
};
D.data=SKILLS;
D.render=function(){
var d=D.data;if(!d)return;
document.getElementById('c-p').textContent=d.pending||0;
document.getElementById('c-a').textContent=d.approved||0;
document.getElementById('c-r').textContent=d.rejected||0;
document.getElementById('s-count').textContent=(d.pending||0)+' items';
var list=document.getElementById('s-list');
if(!d.skills||!d.skills.length){
list.innerHTML='<div class="empty"><div class="prompt">no pending skills<span class="cur"></span></div></div>';
return;
}
var html='';
for(var i=0;i<d.skills.length;i++){
var s=d.skills[i];
var sc=s.decision==='PASS'?'p':s.decision==='REJECT'?'f':'w';
var checks='';
var checksArr=s.checks||[];
for(var j=0;j<checksArr.length;j++){
var c=checksArr[j];var ip=c.indexOf('PASS')>=0;var if2=c.indexOf('FAIL')>=0;
var ic=ip?'p':if2?'f':'i';var ch=ip?'+':if2?'-':'~';
var tc=if2?' f':'';
checks+='<div class="citem"><span class="cicon '+ic+'">'+ch+'</span><span class="ctext'+tc+'">'+this.esc(c)+'</span></div>';
}
html+='<div class="scard"><div class="scard-h"><div class="sidx">'+String(i+1).padStart(2,'0')+':</div><div class="sname">'+this.esc(s.name)+'</div><div class="sscore '+sc+'">'+s.score+'/100</div></div><div class="scard-b"><div class="sdesc">'+this.esc(s.description||'')+'</div><div class="smeta"><div class="smeta-i">decision: <span>'+this.esc(s.decision||'')+'</span></div><div class="smeta-i">size: <span>'+s.size+' chars</span></div></div><button class="ctoggle" data-i="'+i+'"><span class="arr">&gt;</span><span>checks ('+checksArr.length+')</span></button><div class="clist">'+(checks||'<div class="citem"><span class="ctext">no checks</span></div>')+'</div></div></div>';
}
list.innerHTML=html;
var btns=list.querySelectorAll('.ctoggle');
for(var k=0;k<btns.length;k++){
btns[k].addEventListener('click',function(e){e.preventDefault();this.classList.toggle('exp');this.nextElementSibling.classList.toggle('vis');});
}
};
D.esc=function(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML};
document.addEventListener('DOMContentLoaded',function(){D.init()});
</script>
</body>
</html>""".replace("PLACEHOLDER_SKILLS", skills_json)

        return html

    def _generate_markdown(self, pending_skills, approved_count, rejected_count) -> str:
        """Generate Markdown dashboard."""
        md = "# DASHBOARD DE REVISAO DE SKILLS\n\n"
        md += "**Gerado em**: %s\n\n" % datetime.now().strftime('%Y-%m-%d %H:%M')
        md += "| Status | Quantidade |\n|--------|------------|\n"
        md += "| Pendentes | %d |\n" % len(pending_skills)
        md += "| Aprovadas | %d |\n" % approved_count
        md += "| Rejeitadas | %d |\n\n" % rejected_count

        if pending_skills:
            md += "## Skills Pendentes\n\n"
            for i, skill in enumerate(pending_skills, 1):
                icon = "+" if skill['decision'] == 'PASS' else "-" if skill['decision'] == 'REJECT' else "~"
                md += "### %d. %s %s\n\n" % (i, skill['name'], icon)
                md += "- **Score**: %d/100\n" % skill['score']
                md += "- **Decisao**: %s\n" % skill['decision']
                md += "- **Descricao**: %s\n" % skill['description']
                md += "- **Tamanho**: %d chars\n\n" % skill['size']
                md += "**Checks**:\n"
                for check in skill.get('checks', []):
                    icon = "+" if "PASS" in check else "-" if "FAIL" in check else "~"
                    md += "- %s %s\n" % (icon, check)
                md += "\n"
        else:
            md += "## Skills Pendentes\n\n**Nenhuma skill pendente no momento.**\n\n"

        return md

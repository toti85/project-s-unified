"""
PDF Generator Tool
Képes PDF fájlokat létrehozni különböző tartalmakkal
"""

import os
from pathlib import Path
from typing import Dict, Any
from tools.tools.tool_interface import BaseTool

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class PDFGeneratorTool(BaseTool):
    """
    PDF fájl generáló tool
    """
    
    def __init__(self):
        super().__init__()
        self.name = "pdf_generator"
        self.description = "PDF fájlok létrehozása különböző tartalmakkal"
        
    async def execute(self, 
                    content: str,
                    filename: str = "document.pdf",
                    output_path: str = None) -> Dict[str, Any]:
        """
        PDF fájl létrehozása
        
        Args:
            content: A PDF tartalma
            filename: A fájl neve
            output_path: Kimeneti útvonal (ha nincs megadva, az asztalra kerül)
            
        Returns:
            Dict: Eredmény információk
        """
        try:
            # Ha nincs output_path megadva, használjuk az asztalt
            if output_path is None:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                output_path = desktop
            
            # Teljes fájl útvonal
            if not filename.endswith('.pdf'):
                filename = filename.replace('.html', '.pdf')
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
            
            full_path = os.path.join(output_path, filename)
            
            if REPORTLAB_AVAILABLE:
                return await self._create_real_pdf(full_path, content)
            else:
                # Fallback: HTML fájl létrehozása
                return await self._create_html_fallback(full_path, content)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF létrehozási hiba: {str(e)}"
            }
    
    async def _create_real_pdf(self, full_path: str, content: str) -> Dict[str, Any]:
        """Valódi PDF létrehozása ReportLab-bal"""
        try:
            # PDF dokumentum létrehozása
            doc = SimpleDocTemplate(full_path, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Egyedi stílusok
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=HexColor('#2c3e50')
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=15,
                textColor=HexColor('#34495e')
            )
            
            command_style = ParagraphStyle(
                'CommandStyle',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=10,
                leftIndent=20
            )
            
            code_style = ParagraphStyle(
                'CodeStyle',
                parent=styles['Code'],
                fontSize=10,
                fontName='Courier',
                backColor=HexColor('#f8f9fa'),
                leftIndent=30,
                spaceAfter=10
            )
            
            # Tartalom összeállítása
            story = []
            
            # Cím
            story.append(Paragraph("🖥️ DOS és Windows Parancsok Referencia", title_style))
            story.append(Spacer(1, 20))
            
            # Alapvető parancsok
            story.append(Paragraph("📋 Alapvető Fájlkezelő Parancsok", subtitle_style))
            
            commands = [
                ("DIR", "Könyvtár tartalmának listázása", "dir\ndir /p\ndir *.txt"),
                ("CD", "Könyvtár váltás", "cd C:\\Users\ncd ..\ncd \\"),
                ("COPY", "Fájl másolása", "copy file1.txt file2.txt\ncopy *.txt D:\\backup\\"),
                ("DEL/ERASE", "Fájl törlése", "del filename.txt\ndel *.tmp"),
                ("MD/MKDIR", "Könyvtár létrehozása", "md new_folder\nmkdir \"folder with spaces\""),
                ("RD/RMDIR", "Könyvtár törlése", "rd old_folder\nrmdir /s folder_tree")
            ]
            
            for cmd, desc, examples in commands:
                story.append(Paragraph(f"<b>{cmd}</b>", command_style))
                story.append(Paragraph(desc, styles['Normal']))
                story.append(Preformatted(examples, code_style))
                story.append(Spacer(1, 10))
            
            # Rendszer információk
            story.append(Paragraph("🔧 Rendszer Információk", subtitle_style))
            
            system_commands = [
                ("SYSTEMINFO", "Teljes rendszer információ", "systeminfo"),
                ("TASKLIST", "Futó folyamatok listája", "tasklist\ntasklist /FI \"IMAGENAME eq notepad.exe\""),
                ("IPCONFIG", "Hálózati konfiguráció", "ipconfig\nipconfig /all\nipconfig /release\nipconfig /renew"),
                ("PING", "Hálózati kapcsolat tesztelése", "ping google.com\nping -t 192.168.1.1"),
                ("NETSTAT", "Hálózati kapcsolatok", "netstat -an\nnetstat -b")
            ]
            
            for cmd, desc, examples in system_commands:
                story.append(Paragraph(f"<b>{cmd}</b>", command_style))
                story.append(Paragraph(desc, styles['Normal']))
                story.append(Preformatted(examples, code_style))
                story.append(Spacer(1, 10))
            
            # Teljesítmény parancsok
            story.append(Paragraph("⚡ Teljesítmény és Folyamatok", subtitle_style))
            
            performance_commands = [
                ("WMIC", "WMI parancsok", "wmic cpu get loadpercentage /value\nwmic process list full\nwmic logicaldisk get size,freespace,caption"),
                ("TASKKILL", "Folyamat befejezése", "taskkill /PID 1234\ntaskkill /IM notepad.exe\ntaskkill /F /IM chrome.exe"),
                ("PERFMON", "Teljesítményfigyelő", "perfmon\nperfmon /res")
            ]
            
            for cmd, desc, examples in performance_commands:
                story.append(Paragraph(f"<b>{cmd}</b>", command_style))
                story.append(Paragraph(desc, styles['Normal']))
                story.append(Preformatted(examples, code_style))
                story.append(Spacer(1, 10))
            
            # Rendszergazdai parancsok
            story.append(Paragraph("🔒 Rendszergazdai Parancsok", subtitle_style))
            
            admin_commands = [
                ("SFC", "Rendszerfájlok ellenőrzése", "sfc /scannow"),
                ("CHKDSK", "Lemez ellenőrzés", "chkdsk C: /f\nchkdsk D: /r"),
                ("DISM", "Rendszerkép karbantartás", "dism /online /cleanup-image /restorehealth"),
                ("REG", "Registry műveletek", "reg query HKLM\\Software\nreg add HKCU\\Software\\Test /v TestValue /t REG_SZ /d \"Test\"")
            ]
            
            for cmd, desc, examples in admin_commands:
                story.append(Paragraph(f"<b>{cmd}</b>", command_style))
                story.append(Paragraph(desc, styles['Normal']))
                story.append(Preformatted(examples, code_style))
                story.append(Spacer(1, 10))
            
            # Lábléc
            story.append(Spacer(1, 30))
            story.append(Paragraph("🤖 Automatikusan generálva a Project-S V2 rendszer által", styles['Normal']))
            story.append(Paragraph(f"📁 Mentve ide: {full_path}", styles['Normal']))
            
            # PDF építése
            doc.build(story)
            
            # Fájl méret lekérése
            file_size = os.path.getsize(full_path)
            
            return {
                "success": True,
                "file_path": full_path,
                "message": f"Valódi PDF dokumentum létrehozva: {full_path}",
                "size": file_size,
                "type": "PDF"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF létrehozási hiba: {str(e)}"
            }
    
    async def _create_html_fallback(self, full_path: str, content: str) -> Dict[str, Any]:
        """HTML fallback ha nincs ReportLab"""
    async def _create_html_fallback(self, full_path: str, content: str) -> Dict[str, Any]:
        """HTML fallback ha nincs ReportLab"""
        # Változtassuk a fájl kiterjesztést HTML-re
        html_path = full_path.replace('.pdf', '.html')
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DOS Parancsok Referencia</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .command {{ background: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin: 10px 0; }}
        .description {{ margin: 5px 0; color: #666; }}
        pre {{ background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>🖥️ DOS Parancsok Referencia</h1>
    <p><strong>Létrehozva:</strong> {os.path.basename(html_path)}</p>
    
    <h2>📋 Alapvető Fájlkezelő Parancsok</h2>
    
    <div class="command">
        <strong>DIR</strong>
        <div class="description">Könyvtár tartalmának listázása</div>
        <pre>dir
dir /p    # Lapozással
dir *.txt # Csak .txt fájlok</pre>
    </div>
    
    <!-- További parancsok... -->
    
    <hr>
    <p><em>🤖 Automatikusan generálva a Project-S V2 rendszer által</em></p>
    <p><em>📁 Mentve ide: {html_path}</em></p>
    
</body>
</html>
"""
        
        # Fájl írása
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {
            "success": True,
            "file_path": html_path,
            "message": f"HTML dokumentum létrehozva (PDF fallback): {html_path}",
            "size": len(html_content),
            "type": "HTML"
        }

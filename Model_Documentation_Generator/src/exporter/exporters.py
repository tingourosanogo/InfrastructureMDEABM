#!/usr/bin/env python3
"""
Module d'export HTML, PDF et DOCX pour la documentation
"""

import os
import markdown
import pdfkit
from pathlib import Path
import logging
import re
import html
import unicodedata
from typing import Optional, List
from datetime import datetime

# Import conditionnel pour DOCX
try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.shared import qn
    from docx.oxml.ns import nsdecls
    from docx.oxml import parse_xml
    from docx.table import _Cell
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    logging.warning("python-docx non installé. Export DOCX désactivé.")

logger = logging.getLogger(__name__)

class DocumentationExporter:
    """Classe pour exporter la documentation en différents formats"""
    
    def __init__(self, wkhtmltopdf_path: Optional[str] = None):
        self.wkhtmltopdf_path = wkhtmltopdf_path
        self._configure_pdfkit()
    
    def _configure_pdfkit(self):
        """Configure pdfkit avec le chemin de wkhtmltopdf"""
        if self.wkhtmltopdf_path and os.path.exists(self.wkhtmltopdf_path):
            self.config = pdfkit.configuration(wkhtmltopdf_path=self.wkhtmltopdf_path)
        else:
            try:
                self.config = pdfkit.configuration()
            except Exception as e:
                logger.warning(f"wkhtmltopdf non trouvé: {e}. PDF export désactivé.")
                self.config = None

    def markdown_to_html(self, markdown_content: str, output_path: str, css_path: Optional[str] = None) -> bool:
        """
        Convertit le Markdown en HTML
        
        Args:
            markdown_content: Contenu Markdown à convertir
            output_path: Chemin du fichier HTML de sortie
            css_path: Chemin vers un fichier CSS personnalisé (optionnel)
        
        Returns:
            bool: True si la conversion réussit
        """
        try:
            # Convertir Markdown en HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=['extra', 'tables', 'fenced_code', 'codehilite']
            )
            
            # Créer le HTML complet avec CSS
            full_html = self._wrap_html(html_content, css_path)
            
            # Écrire le fichier HTML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            logger.info(f"HTML generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur conversion HTML: {e}")
            return False

    def markdown_to_pdf(self, markdown_content: str, output_path: str, css_path: Optional[str] = None) -> bool:
        """
        Convertit le Markdown en PDF via HTML
        
        Args:
            markdown_content: Contenu Markdown à convertir
            output_path: Chemin du fichier PDF de sortie
            css_path: Chemin vers un fichier CSS personnalisé (optionnel)
        
        Returns:
            bool: True si la conversion réussit
        """
        if not self.config:
            logger.error("wkhtmltopdf non configuré. Impossible de générer PDF.")
            return False
        
        try:
            # D'abord convertir en HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=['extra', 'tables', 'fenced_code', 'codehilite']
            )
            
            full_html = self._wrap_html(html_content, css_path)
            
            # Options de configuration PDF
            options = {
                'page-size': 'A4',
                'margin-top': '20mm',
                'margin-right': '15mm',
                'margin-bottom': '20mm',
                'margin-left': '15mm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None  # Permet l'accès aux fichiers locaux
            }
            
            # Convertir HTML en PDF
            pdfkit.from_string(
                full_html, 
                output_path, 
                configuration=self.config,
                options=options
            )
            
            logger.info(f"PDF generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur conversion PDF: {e}")
            return False

    def _clean_content_keep_unicode(self, content: str) -> str:
        """
        Nettoie le contenu tout en conservant les caractères Unicode (é, à, è, etc.)
        
        Args:
            content: Contenu à nettoyer
        
        Returns:
            str: Contenu nettoyé mais avec Unicode préservé
        """
        if not content:
            return ""
        
        # Supprimer seulement les caractères de contrôle dangereux (NULL bytes, etc.)
        # Mais conserver tous les caractères Unicode valides
        content = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', content)
        
        # Normaliser les sauts de ligne
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Nettoyer les problèmes d'encodage courants
        content = self._fix_common_encoding_issues(content)
        
        return content

    def _fix_common_encoding_issues(self, content: str) -> str:
        """
        Corrige les problèmes d'encodage courants sans perdre l'Unicode
        """
        # Remplace les séquences UTF-8 mal formées
        content = content.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
        
        # Normalise l'Unicode (NFC forme canonique)
        content = unicodedata.normalize('NFC', content)
        
        # Corrige les problèmes de guillemets
        content = content.replace('â€œ', '"').replace('â€', '"')  # Guillemets courbes
        content = content.replace('â€™', "'").replace('â€˜', "'")  # Apostrophes
        
        return content


    def _wrap_html(self, html_content: str, css_path: Optional[str] = None) -> str:
        """
        Encapsule le contenu HTML dans un template complet - VERSION CORRIGÉE
        """
        # CSS par défaut intégré
        default_css = """
        <style>
            body { font-family: 'Arial', sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }
            h1, h2, h3, h4, h5, h6 { color: #2c3e50; margin-top: 1.5em; margin-bottom: 0.5em; }
            h1 { border-bottom: 2px solid #3498db; padding-bottom: 0.3em; }
            h2 { border-bottom: 1px solid #ecf0f1; padding-bottom: 0.2em; }
            code { background-color: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
            pre { background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; border-left: 4px solid #3498db; }
            table { border-collapse: collapse; width: 100%; margin: 1em 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .header { text-align: center; margin-bottom: 2em; padding: 1em; background: #667eea; color: white; }
            .footer { text-align: center; margin-top: 3em; padding: 1em; border-top: 1px solid #ecf0f1; color: #7f8c8d; }
        </style>
        """
        
        # Charger CSS personnalisé si spécifié
        custom_css = ""
        if css_path and os.path.exists(css_path):
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    custom_css = f"<style>\n{f.read()}\n</style>"
            except Exception as e:
                logger.warning(f"Erreur lecture CSS {css_path}: {e}")
        
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document de spécification</title>
    {default_css}
    {custom_css}
</head>
<body>
    <div class="header">
        <h1>Document de spécification</h1>
        <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
    </div>
    
    <div class="content">
        {html_content}
    </div>
    
    <div class="footer">
        <p>Document généré automatiquement avec CIM-PIM Transformation Tool</p>
    </div>
</body>
</html>"""

    # Ajouter cette méthode pour gérer la fin de document
    def _finalize_document(self, doc: Document):
        """Nettoie les espaces vides excessifs à la fin du document"""
        # Supprimer les paragraphes vides en fin de document
        while doc.paragraphs and not doc.paragraphs[-1].text.strip():
            p = doc.paragraphs[-1]
            p_element = p._element
            p_element.getparent().remove(p_element)
        
        # S'assurer que le document ne se termine pas par trop d'espaces
        if doc.paragraphs:
            last_paragraph = doc.paragraphs[-1]
            if not last_paragraph.text.strip():
                p_element = last_paragraph._element
                p_element.getparent().remove(p_element)

    def markdown_to_docx(self, markdown_content: str, output_path: str) -> bool:
        """
        Convertit le Markdown en DOCX avec mise en page professionnelle
        
        Args:
            markdown_content: Contenu Markdown à convertir
            output_path: Chemin du fichier DOCX de sortie
        
        Returns:
            bool: True si la conversion réussit
        """
        if not HAS_DOCX:
            logger.error("python-docx non installé. Impossible d'exporter en DOCX.")
            print("Export DOCX nécessite: pip install python-docx")
            return False
        
        try:
            # Créer le document Word avec mise en page professionnelle
            doc = Document()
            
            # Configuration de la mise en page
            self._setup_professional_layout(doc)

            # Extraire le contenu de la page de garde (entre les ---)
            cover_content = self._extract_cover_content(markdown_content)
            
            if cover_content:
                # Créer une page de garde professionnelle
                self._create_professional_cover_page(doc, cover_content)
            
                # Ajouter un saut de page
                doc.add_page_break()
                
                # Traiter le reste du contenu
                remaining_content = self._remove_cover_content(markdown_content)
                
                # Extraire et ajouter la table des matières depuis le Markdown
                toc_lines = self._extract_toc_from_markdown(remaining_content)
                if toc_lines:
                    self._add_table_of_contents(doc, toc_lines)

                self._parse_markdown_professional(remaining_content, doc)
            else:
                # Pas de page de garde détectée, traiter tout le contenu
                # Extraire et ajouter la table des matières depuis le Markdown
                toc_lines = self._extract_toc_from_markdown(markdown_content)
                if toc_lines:
                    self._add_table_of_contents(doc, toc_lines)

                self._parse_markdown_professional(markdown_content, doc)

                        
            # Ajouter les en-têtes et pieds de page professionnels
            #self._add_professional_headers_footers(doc)

            # Nettoyer les espaces excessifs
            self._finalize_document(doc)
            
            # Sauvegarder le document
            doc.save(output_path)
            
            logger.info(f"DOCX generated: {output_path}")
            print(f"DOCX generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur conversion DOCX professionnel: {e}")
            print(f"Erreur lors de la génération DOCX: {e}")
            return False

    def _extract_toc_from_markdown(self, markdown_content: str) -> List[str]:
        """
        Extrait la table des matières du contenu Markdown
        """
        toc_lines = []
        lines = markdown_content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            # Détecter les lignes de table des matières
            line_number = f"{i}. ['"
            if line.startswith(line_number) and ". ['" in line and '](#' in line and ')' in line:
                toc_lines.append(line)
            # S'arrêter à la fin de la table des matières
            elif toc_lines and not line.startswith(('1. [', '2. [', '3. [', '4. [', '5. [', '- [')):
                break
        
        return toc_lines

    def _add_table_of_contents(self, doc: Document, toc_lines: List[str]):
        """
        Ajoute une table des matières formatée au document Word
        """
        # Titre de la table des matières
        toc_heading = doc.add_heading('Table des Matières', level=1)
        toc_heading.style = 'Heading 1'
        
        # Ajouter un saut de ligne
        doc.add_paragraph()
        
        # Créer un tableau pour la table des matières
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        
        # En-têtes du tableau
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Section'
        hdr_cells[1].text = 'Page'
        
        # Mettre en forme l'en-tête
        for cell in hdr_cells:
            cell.paragraphs[0].runs[0].bold = True
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Ajouter les entrées de la table des matières
        for toc_line in toc_lines:
            # Parser la ligne de table des matières
            if '[' in toc_line and '](' in toc_line and ')' in toc_line:
                # Extraire le texte et le lien
                start_idx = toc_line.find('[') + 1
                end_idx = toc_line.find(']')
                link_start = toc_line.find('(') + 1
                link_end = toc_line.find(')')
                
                if start_idx != -1 and end_idx != -1 and link_start != -1 and link_end != -1:
                    section_name = toc_line[start_idx:end_idx]
                    section_link = toc_line[link_start:link_end]
                    
                    # Ajouter une nouvelle ligne au tableau
                    row_cells = table.add_row().cells
                    row_cells[0].text = section_name
                    row_cells[1].text = ""  # Le numéro de page sera rempli automatiquement
                    
                    # Ajouter un champ de renvoi pour la pagination
                    self._add_pagination_field(row_cells[1], section_link)
        
        # Ajouter un saut de page après la table des matières
        doc.add_page_break()

    def _add_pagination_field(self, cell, bookmark_name: str):
        """
        Ajoute un champ de pagination pour la table des matières
        """
        # Nettoyer le nom du bookmark (enlever le #)
        clean_bookmark = bookmark_name.replace('#', '').replace('(', '').replace(')', '')
        
        # Créer le XML pour le champ PAGEREF
        field_code = f' PAGEREF {clean_bookmark} \\h '
        
        # Ajouter le champ au document
        paragraph = cell.paragraphs[0]
        run = paragraph.add_run()
        run._element.append(parse_xml(
            f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f'<w:fldChar w:fldCharType="begin"/></w:r>'
        ))
        
        run = paragraph.add_run()
        run._element.append(parse_xml(
            f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f'<w:instrText xml:space="preserve">{field_code}</w:instrText></w:r>'
        ))
        
        run = paragraph.add_run()
        run._element.append(parse_xml(
            f'<w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f'<w:fldChar w:fldCharType="end"/></w:r>'
        ))

    def _add_bookmarks_to_headings(self, doc: Document):
        """
        Ajoute des bookmarks aux titres pour la table des matières
        """
        bookmark_id = 1
        for paragraph in doc.paragraphs:
            if paragraph.style.name.startswith('Heading'):
                # Créer un bookmark pour ce titre
                bookmark_name = f"heading_{bookmark_id}"
                self._add_bookmark(paragraph, bookmark_name)
                bookmark_id += 1

    def _add_bookmark(self, paragraph, bookmark_name: str):
        """
        Ajoute un bookmark à un paragraphe
        """
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
        run._element.append(parse_xml(
            f'<w:bookmarkStart w:id="{bookmark_name}" w:name="{bookmark_name}" '
            f'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'
        ))
        
        # Ajouter aussi la fin du bookmark
        run._element.append(parse_xml(
            f'<w:bookmarkEnd w:id="{bookmark_name}" '
            f'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'
        ))

    def _update_fields(self, doc: Document):
        """
        Met à jour tous les champs du document (pour actualiser la pagination)
        """
        # Cette fonction permet d'actualiser les champs de pagination
        # Word le fera automatiquement à l'ouverture, mais on peut forcer l'update
        for paragraph in doc.paragraphs:
            for run in paragraph.runs:
                if run.text and 'PAGEREF' in run.text:
                    # Marquer le champ comme à mettre à jour
                    pass

    def _extract_cover_content(self, markdown_content: str) -> Optional[str]:
        """
        Extrait le contenu entre les premiers --- du Markdown
        """
        lines = markdown_content.split('\n')
        cover_lines = []
        in_cover = False
        cover_delimiter_count = 0
        
        for line in lines:
            if line.strip() == '---':
                cover_delimiter_count += 1
                if cover_delimiter_count == 1:
                    in_cover = True
                    continue
                elif cover_delimiter_count == 2:
                    break
            
            if in_cover and cover_delimiter_count == 1:
                cover_lines.append(line)
        
        return '\n'.join(cover_lines) if cover_lines else None

    def _remove_cover_content(self, markdown_content: str) -> str:
        """
        Retire le contenu de la page de garde du Markdown
        """
        lines = markdown_content.split('\n')
        result_lines = []
        in_cover = False
        cover_delimiter_count = 0
        
        for line in lines:
            if line.strip() == '---':
                cover_delimiter_count += 1
                if cover_delimiter_count == 2:
                    in_cover = False
                continue
            
            if cover_delimiter_count < 2:
                continue
                
            result_lines.append(line)
        
        return '\n'.join(result_lines)

    def _create_professional_cover_page(self, doc: Document, cover_content: str):
        """
        Orchestre la création de la page de garde professionnelle.
        """
        # Configuration des marges
        section = doc.sections[0]
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

        # Ajout des composants
        self._add_cover_header(doc)
        #self._add_main_title(doc, "Document de spécification")
        #self._add_subtitle(doc, "Spécifications du Modèle Conceptuel")
        doc.add_paragraph().add_run("").font.size = Pt(72)
        self._add_styled_content(doc, cover_content)
        self._add_professional_footer(doc)

    def _add_cover_header(self, doc: Document):
        """
        Ajoute un en-tête avec bandeau coloré moderne
        """
        # Bandeau bleu en haut de page
        header_para = doc.add_paragraph()
        header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        
        # Fond coloré pour le bandeau (simulé par un tableau)
        table = doc.add_table(rows=1, cols=1)
        cell = table.cell(0, 0)
        table.autofit = False
        table.columns[0].width = Inches(6.5)
        
        # Appliquer le fond bleu
        cell = table.cell(0, 0)
        shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="0078D4"/>')  # Bleu Microsoft
        cell._tc.get_or_add_tcPr().append(shading_elm)
        
        # Ajoute le texte dans la cellule et le style en une seule fois
        header_para = cell.add_paragraph("Document de spécification")
        header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_para.paragraph_format.space_after = Pt(10)
        run = header_para.runs[0]
        run.font.size = Pt(32)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.name = 'Calibri Light'
        
        # Supprimer les bordures du tableau
        self._remove_table_borders(table)

    def _add_main_title(self, doc: Document, title: str):
        """
        Ajoute le titre avec un effet d'ombre. Utilise une superposition élégante et robuste.
        """
        doc.add_paragraph().add_run("").font.size = Pt(24) # Ajustement de l'espacement initial

        
        # Ajout du titre principal avec superposition
        main_para = doc.add_paragraph()
        main_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        main_para.paragraph_format.space_before = Pt(32) # Espacement négatif pour la superposition
        main_run = main_para.add_run(title)
        main_run.font.size = Pt(20)
        main_run.font.bold = True
        main_run.font.color.rgb = RGBColor(51, 51, 51) 
        main_run.font.name = 'Calibri Light'

    def _add_subtitle(self, doc: Document, subtitle: str):
        """
        Ajoute un sous-titre élégant
        """
        subtitle_para = doc.add_paragraph()
        subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_para.paragraph_format.space_before = Pt(8)
        
        subtitle_run = subtitle_para.add_run(subtitle)
        subtitle_run.font.size = Pt(18)
        subtitle_run.font.color.rgb = RGBColor(102, 102, 102)  # Gris foncé
        subtitle_run.font.name = 'Calibri'
        subtitle_run.font.bold = True

    def _add_subsubtitle(self, doc: Document, subtitle: str):
        """
        Ajoute un sous-titre élégant
        """
        subtitle_para = doc.add_paragraph()
        subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_para.paragraph_format.space_before = Pt(8)
        
        subtitle_run = subtitle_para.add_run(subtitle)
        subtitle_run.font.size = Pt(14)
        subtitle_run.font.color.rgb = RGBColor(45, 45, 45)  
        subtitle_run.font.name = 'Calibri'
        subtitle_run.font.bold = True

    def _add_styled_content(self, doc: Document, content: str):
        """
        Ajoute le contenu dans un cadre stylisé moderne
        """
        # Créer un tableau pour le cadre
        table = doc.add_table(rows=1, cols=1)
        #table.style = 'Table Grid'
        table.autofit = False
        table.columns[0].width = Inches(5)
        
        # Style du cadre
        cell = table.cell(0, 0)
        shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8F9FA"/>')  # Fond gris très clair
        cell._tc.get_or_add_tcPr().append(shading_elm)
        
        # Bordures stylisées
        tbl_borders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>'
            f'<w:left w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>'
            f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>'
            f'<w:right w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>'
            f'</w:tblBorders>'
        )
        table._tbl.tblPr.append(tbl_borders)
        
        # Ajouter le contenu formaté
        self._add_formatted_cover_content(cell, content)

    def _add_formatted_cover_content(self, cell, content: str):
        """
        Ajoute le contenu formaté dans la cellule
        """
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            clean_line = self._clean_markdown_formatting(line)
            
            if line.startswith('# '):
                self._add_content_title(cell, line[2:])
            elif line.startswith('## '):
                self._add_content_subtitle(cell, line[3:])
            elif line.startswith('### '):
                self._add_content_subsubtitle(cell, line[4:])
            elif line.startswith('**') and line.endswith('**'):
                self._add_content_highlight(cell, clean_line[2:-2])
            #elif ':' in line:
            #    self._add_content_key_value(cell, clean_line)
            else:
                self._add_content_paragraph(cell, clean_line)

    def _add_content_title(self, cell, text: str):
        """Titre de section dans le contenu"""
        para = cell.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(text.upper())
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 120, 212)  # Bleu Microsoft
        run.font.name = 'Calibri'
        para.paragraph_format.space_after = Pt(12)

    def _add_content_subtitle(self, cell, text: str):
        """Sous-titre de section"""
        para = cell.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(text)
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RGBColor(51, 51, 51)
        run.font.name = 'Calibri'
        para.paragraph_format.space_before = Pt(10)
        para.paragraph_format.space_after = Pt(2)

    def _add_content_subsubtitle(self, cell, text: str):
        """Sous-titre de section"""
        para = cell.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(text)
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor(102, 102, 102)
        run.font.name = 'Calibri'
        para.paragraph_format.space_before = Pt(10)
        para.paragraph_format.space_after = Pt(4)

    def _add_content_highlight(self, cell, text: str):
        """Texte en évidence"""
        para = cell.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(text)
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 102, 204)
        run.font.name = 'Calibri'
        para.paragraph_format.space_after = Pt(6)

    def _add_content_key_value(self, cell, line: str):
        """Paire clé-valeur formatée"""
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Tableau à 2 colonnes pour l'alignement
            kv_table = cell.add_table(rows=1, cols=2)
            kv_table.autofit = False
            kv_table.columns[0].width = Inches(1.8)
            kv_table.columns[1].width = Inches(2.2)
            
            # Supprimer les bordures
            self._remove_table_borders(kv_table)
            
            # Cellule clé (alignée à droite)
            key_cell = kv_table.cell(0, 0)
            key_cell.text = key
            key_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
            key_cell.paragraphs[0].runs[0].font.size = Pt(10)
            key_cell.paragraphs[0].runs[0].font.bold = True
            key_cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(102, 102, 102)
            
            # Cellule valeur (alignée à gauche)
            value_cell = kv_table.cell(0, 1)
            value_cell.text = value
            value_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
            value_cell.paragraphs[0].runs[0].font.size = Pt(10)
            value_cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0, 0, 0)

    def _add_content_paragraph(self, cell, text: str):
        """Paragraphe normal"""
        if text.strip():
            para = cell.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(text)
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(102, 102, 102)
            run.font.name = 'Calibri'
            para.paragraph_format.space_after = Pt(2)
     

    def _add_professional_footer(self, doc: Document):
        """
        Ajoute un pied de page professionnel avec design moderne
        """
        # Espacement
        for _ in range(4):
            doc.add_paragraph().add_run("").font.size = Pt(12)
        
        # Ligne de séparation stylisée
        line_table = doc.add_table(rows=1, cols=1)
        line_table.autofit = False
        line_table.columns[0].width = Inches(3)
        
        line_cell = line_table.cell(0, 0)
        line_cell.text = "─" * 35  # Ligne Unicode
        line_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        line_cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(200, 200, 200)
        line_cell.paragraphs[0].runs[0].font.size = Pt(10)
        
        self._remove_table_borders(line_table)
        
        # Informations de génération avec icônes
        info_para = doc.add_paragraph()
        info_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        info_para.paragraph_format.space_before = Pt(1)
        
        info_text = (
            f"📅 Généré le {datetime.now().strftime('%d/%m/%Y')} | "
            f"🔄 Version 1.0 | "
            f"⚙️ CIM-PIM Transformation Tool"
        )
        
        info_run = info_para.add_run(info_text)
        info_run.font.size = Pt(9)
        info_run.font.color.rgb = RGBColor(153, 153, 153)
        info_run.font.name = 'Consolas'
        
        # Copyright et watermark discret
        copyright_text = f"© {datetime.now().strftime('%Y')} - Document de spécification"
        copyright_para = doc.add_paragraph()
        copyright_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        copyright_run = copyright_para.add_run(copyright_text)
        copyright_run.font.size = Pt(8)
        copyright_run.font.color.rgb = RGBColor(180, 180, 180)
        copyright_run.font.italic = True

    def _remove_table_borders(self, table):
        """Supprime toutes les bordures d'un tableau"""
        tbl = table._tbl
        tblPr = tbl.tblPr
        
        # Supprimer les bordures
        tblBorders = parse_xml(r'<w:tblBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                              r'<w:top w:val="nil" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:left w:val="nil" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:bottom w:val="nil" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:right w:val="nil" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:insideH w:val="nil" w:sz="0" w:space="0" w:color="auto"/>'
                              r'<w:insideV w:val="nil" w:sz="0" w:space="0" w:color="auto"/>'
                              r'</w:tblBorders>')
        
        # Ajouter ou remplacer les bordures existantes
        existing_borders = tblPr.find(qn('w:tblBorders'))
        if existing_borders is not None:
            tblPr.replace(existing_borders, tblBorders)
        else:
            tblPr.append(tblBorders)


    def _setup_professional_layout(self, doc: Document):
        """Configure les styles par défaut avec justification"""
        styles = doc.styles

        # 1 --

        # Marges (en pouces: 1 pouce = 914400 EMU)
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
            section.header_distance = Inches(0.5)
            section.footer_distance = Inches(0.5)
        
        # Styles professionnels
        styles = doc.styles
        
        # Style Normal
        normal_style = styles['Normal']
        normal_font = normal_style.font
        normal_font.name = 'Calibri'
        normal_font.size = Pt(11)
        normal_font.color.rgb = RGBColor(0x00, 0x00, 0x00)  # Noir
        normal_style.paragraph_format.space_after = Pt(6)
        normal_style.paragraph_format.line_spacing = 1.15
        
        # Styles de titres
        heading_styles = {
            'Heading 1': {'size': 16, 'bold': True, 'color': RGBColor(0x2E, 0x75, 0xB6), 'space_before': 12, 'space_after': 12},
            'Heading 2': {'size': 14, 'bold': True, 'color': RGBColor(0x2E, 0x75, 0xB6), 'space_before': 10, 'space_after': 10},
            'Heading 3': {'size': 12, 'bold': True, 'color': RGBColor(0x44, 0x72, 0xC4), 'space_before': 8, 'space_after': 8},
            'Heading 4': {'size': 11, 'bold': True, 'color': RGBColor(0x5B, 0x9B, 0xD5), 'space_before': 6, 'space_after': 6}
        }
        
        for style_name, config in heading_styles.items():
            if style_name in styles:
                style = styles[style_name]
                style.font.name = 'Calibri'
                style.font.size = Pt(config['size'])
                style.font.bold = config['bold']
                style.font.color.rgb = config['color']
                style.paragraph_format.space_after = Pt(config['space_after'])
                style.paragraph_format.space_before = Pt(config['space_before'])

        
        # 2 -- Style pour le corps de texte justifié
        if 'Normal' in styles:
            normal_style = styles['Normal']
            normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        else:
            # Créer le style Normal s'il n'existe pas
            normal_style = styles.add_style('Normal', 1)
            normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        # Style pour le titre principal (centré)
        if 'Titre Principal' not in styles:
            title_style = styles.add_style('Titre Principal', 1)
            title_style.font.size = Pt(16)
            title_style.font.bold = True
            title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Style pour les blocs de code (aligné à gauche)
        if 'Code Block' in styles:
            code_style = styles['Code Block']
            code_style.font.name = 'Courier New'
            code_style.font.size = Pt(9)
            code_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            code_style.paragraph_format.left_indent = Inches(0.2)
        else:
            code_style = styles.add_style('Code Block', 1)
            code_style.font.name = 'Courier New'
            code_style.font.size = Pt(9)
            code_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            code_style.paragraph_format.left_indent = Inches(0.2)
        
        # Style pour les citations (justifié avec indentation)
        if 'Quote' in styles:
            quote_style = styles['Quote']
            quote_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            #quote_style.paragraph_format.left_indent = Inches(0.2)
            #quote_style.paragraph_format.right_indent = Inches(0.2)
        else:
            quote_style = styles.add_style('Quote', 1)
            quote_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            #quote_style.paragraph_format.left_indent = Inches(0.2)
            #quote_style.paragraph_format.right_indent = Inches(0.2)

        if 'Citation' in styles:
            quote_style = styles['Citation']
            quote_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            #quote_style.paragraph_format.left_indent = Inches(0.2)
            #quote_style.paragraph_format.right_indent = Inches(0.2)
        else:
            quote_style = styles.add_style('Citation', 1)
            quote_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            #quote_style.paragraph_format.left_indent = Inches(0.2)
            #quote_style.paragraph_format.right_indent = Inches(0.2)
        



    def _parse_markdown_professional(self, markdown_content: str, doc: Document):
        """Parse le Markdown avec une mise en forme professionnelle"""
        lines = markdown_content.split('\n')
        in_code_block = False
        in_table = False
        last_was_blank = False
        table_rows = []
        current_list_level = 0
        heading_count = 0
        
        for i, line in enumerate(lines):
            line = line.rstrip()

            # Ignorer la table des matières du Markdown
            if (line.startswith('1. [') or line.startswith('- [')) and '](#' in line:
                continue
            
            # Gestion des blocs de code
            if line.strip().startswith('```'):
                if in_code_block:
                    self._add_professional_code_block(doc, '\n'.join(code_lines))
                    in_code_block = False
                    last_was_blank = False
                else:
                    in_code_block = True
                    code_lines = []
                continue
            
            if in_code_block:
                code_lines.append(line)
                #last_was_blank = False
                continue
            
            # Ignorer les lignes totalement vides consécutives
            if line.strip() == '':
                if not last_was_blank:
                    last_was_blank = True
                    continue
                else:
                    last_was_blank = False

            # Gestion des tableaux
            if '|' in line:
                if '--' in line:  # Ligne de séparation du tableau
                    in_table = True
                    continue
                elif in_table:
                    table_rows.append(line)
                    continue
                else:
                    # Détection d'un nouveau tableau
                    if not in_table and line.count('|') >= 2:
                        in_table = True
                        table_rows = [line]
                        continue
            
            # Fin d'un tableau
            if in_table and not line.strip():
                self._add_professional_table(doc, table_rows)
                in_table = False
                table_rows = []
                continue
            
            if in_table:
                table_rows.append(line)
                continue
            
            # Gestion des titres
            if line.startswith('# '):
                heading_count += 1
                self._add_heading_with_bookmark(doc, line[2:], 1, f"heading_{heading_count}")
                last_was_blank = False
            elif line.startswith('## '):
                heading_count += 1
                self._add_heading_with_bookmark(doc, line[3:], 2, f"heading_{heading_count}")
                last_was_blank = False
            elif line.startswith('### '):
                heading_count += 1
                self._add_heading_with_bookmark(doc, line[4:], 3, f"heading_{heading_count}")
                last_was_blank = False
            elif line.startswith('#### '):
                heading_count += 1
                self._add_heading_with_bookmark(doc, line[5:], 4, f"heading_{heading_count}")
                last_was_blank = False
            elif line.startswith('##### '):
                heading_count += 1
                self._add_heading_with_bookmark(doc, line[6:], 5, f"heading_{heading_count}")
                last_was_blank = False
            elif line.startswith('###### '):
                heading_count += 1
                self._add_heading_with_bookmark(doc, line[7:], 6, f"heading_{heading_count}")
                last_was_blank = False
            
            # Gestion des listes
            elif line.strip().startswith('- '):
                self._add_professional_list_item(doc, line.strip()[2:], 1)
                last_was_blank = False
            
            # Gestion des images (format basique)
            elif '![' in line and '](' in line and line.endswith(')'):
                self._add_professional_image(doc, line)
                last_was_blank = False
            
            
            # Lignes de séparation centrées
            elif line.strip() == '---' or line.strip() == '***':
                self._add_separator(doc)
                
            
            # Paragraphes normaux
            else:
                self._add_professional_paragraph(doc, line)
                last_was_blank = False

    def _add_heading_with_bookmark(self, doc: Document, text: str, level: int, bookmark_name: str):
        """
        Ajoute un titre avec un bookmark pour la table des matières
        """
        heading = doc.add_heading(text, level)
        
        # Ajouter le bookmark
        run = heading.runs[0] if heading.runs else heading.add_run(text)
        self._add_bookmark_to_run(run, bookmark_name)
        
        if level == 1:
            heading.style = 'Heading 1'
        elif level == 2:
            heading.style = 'Heading 2'

    def _add_bookmark_to_run(self, run, bookmark_name: str):
        """
        Ajoute un bookmark à un run spécifique
        """
        run._element.append(parse_xml(
            f'<w:bookmarkStart w:id="{bookmark_name}" w:name="{bookmark_name}" '
            f'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'
        ))
        
        # Ajouter aussi la fin du bookmark
        run._element.append(parse_xml(
            f'<w:bookmarkEnd w:id="{bookmark_name}" '
            f'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'
        ))


    def _add_professional_paragraph(self, doc: Document, text: str):
        """Ajoute un paragraphe professionnel"""
        if not text.strip():
            return
            
        clean_text = self._clean_text(text)
        
        # Gestion du texte formaté (gras, italique)
        if '**' in clean_text or '*' in clean_text or '***' in clean_text:
            para = doc.add_paragraph()
            parts = re.split(r'(\*\*.+?\*\*|\*.+?\*)', clean_text)
            
            for part in parts:
                if not part:
                    continue
                    
                if part.startswith('**') and part.endswith('**'):
                    # Texte en gras
                    run = para.add_run(part[2:-2])
                    run.bold = True
                    run.font.name = 'Calibri'
                elif part.startswith('*') and part.endswith('*'):
                    # Texte en italique
                    run = para.add_run(part[1:-1])
                    run.italic = True
                    run.font.name = 'Calibri'
                elif part.startswith('***') and part.endswith('***'):
                    # Texte en italique et gras
                    run = para.add_run(part[3:-3])
                    run.bold = True
                    run.italic = True
                    run.font.name = 'Calibri'
                else:
                    # Texte normal
                    run = para.add_run(part)
                    run.font.name = 'Calibri'
        else:
            # Texte simple
            para = doc.add_paragraph(clean_text)
            for run in para.runs:
                run.font.name = 'Calibri'

    def _add_professional_list_item(self, doc: Document, text: str, level: int):
        """Ajoute un élément de liste professionnel"""
        if not text.strip():
            return
            
        clean_text = self._clean_text(text)
        
        # Utiliser le style de liste approprié
        if level == 1:
            para = doc.add_paragraph(clean_text, style='List Bullet')
        else:
            para = doc.add_paragraph(clean_text, style='List Number')
        
        # Formatage de la police
         # Appliquer le formatage aux éléments de liste
        self._apply_formatting_to_list(para, clean_text)
        """
        for run in para.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(10)  # Taille légèrement réduite pour les listes
        """

    def _apply_formatting_to_list(self, paragraph, text: str):
        """Applique le formatage à un paragraphe existant"""
        # Clear existing text to re-add with formatting
        paragraph.text = ''
        
        parts = re.split(r'(\*\*.*?\*\*|\*.*?\*|_.*?_)', text)
        
        for part in parts:
            if not part:
                continue
                
            # Texte en gras
            if part.startswith('**') and part.endswith('**'):
                run = paragraph.add_run(part[2:-2])
                run.bold = True
            # Texte en italique
            elif part.startswith('*') and part.endswith('*'):
                run = paragraph.add_run(part[1:-1])
                run.italic = True
            elif part.startswith('_') and part.endswith('_'):
                run = paragraph.add_run(part[1:-1])
                run.italic = True
            # Texte normal
            else:
                paragraph.add_run(part)

    def _add_professional_code_block(self, doc: Document, code: str):
        """Ajoute un bloc de code professionnel"""
        if not code.strip():
            return
            
        # Ajouter un titre pour le bloc de code
        #code_title = doc.add_paragraph("Exemple de code:")
        #code_title.style = 'Heading 4'
        
        # Ajouter le code dans une zone formatée
        code_para = doc.add_paragraph()
        code_para.style = 'Quote'
        
        run = code_para.add_run(code.strip())
        run.font.name = 'Consolas'  # Police monospace professionnelle
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x00, 0x40, 0x00)  # Vert foncé pour le code
        
        # Ajouter un fond gris léger
        shading_elm = parse_xml(r'<w:shd {} w:fill="F5F5F5"/>'.format(nsdecls('w')))
        code_para._element.get_or_add_pPr().append(shading_elm)
        
        # Espacement après le bloc de code
        doc.add_paragraph()

    def _add_professional_table(self, doc: Document, table_rows: list):
        """Ajoute un tableau professionnel"""
        if not table_rows:
            return
            
        # Compter les colonnes
        first_row = table_rows[0]
        col_count = len([cell for cell in first_row.split('|') if cell.strip()])
        
        if col_count == 0:
            return
        
        # Créer le tableau
        table = doc.add_table(rows=1, cols=col_count)
        table.style = 'Table Grid'
        
        # Ajouter l'en-tête
        header_cells = table.rows[0].cells
        headers = [cell.strip() for cell in first_row.split('|') if cell.strip()]
        
        for i, header in enumerate(headers):
            if i < col_count:
                
                # Formater l'en-tête
                cleaned_header = self._clean_markdown_formatting(header)
                header_cells[i].text = cleaned_header
                for paragraph in header_cells[i].paragraphs:
                    for run in paragraph.runs:
                        run.bold = True
                        run.font.name = 'Calibri'
                        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)  # Blanc
                # Fond bleu pour l'en-tête
                shading_elm = parse_xml(r'<w:shd {} w:fill="2E75B6"/>'.format(nsdecls('w')))
                header_cells[i]._element.get_or_add_tcPr().append(shading_elm)
        
        # Ajouter les lignes de données
        for row_data in table_rows[1:]:
            if not row_data.strip():
                continue
                
            cells = [cell.strip() for cell in row_data.split('|') if cell.strip()]
            if len(cells) != col_count:
                continue
                
            row_cells = table.add_row().cells
            for i, cell_text in enumerate(cells):
                if i < col_count:
                    cleaned_text = self._clean_markdown_formatting(cell_text)
                    row_cells[i].text = cleaned_text
                    # Formater les cellules
                    for paragraph in row_cells[i].paragraphs:
                        for run in paragraph.runs:
                            run.font.name = 'Calibri'
                            run.font.size = Pt(10)
        
        # Espacement après le tableau
        doc.add_paragraph()


    def _add_separator(self, doc: Document):
        """Ajoute une ligne de séparation centrée"""
        p = doc.add_paragraph()
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("―" * 40)  # Ligne de séparation
        run.font.color.rgb = None  # Couleur par défaut
        run.font.size = Pt(10)


    def _clean_markdown_formatting(self, text: str) -> str:
        """
        Nettoie le formatage Markdown du texte
        
        Args:
            text: Texte avec formatage Markdown
            
        Returns:
            str: Texte nettoyé
        """
        if not text:
            return text
        
        # Supprimer le gras **texte** → texte
        text = text.replace('**', '')
        
        # Supprimer l'italique *texte* → texte
        text = text.replace('*', '')
        
        # Supprimer le code `texte` → texte
        text = text.replace('`', '')
        
        # Nettoyer les espaces
        text = text.strip()
        
        # Gérer les entités HTML simples (optionnel)
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'"
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)

        """
        Nettoie le texte des formatages Markdown tout en conservant la sémantique
        """
        # Supprimer les astérisques d'italique et de gras
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Gras
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italique
        text = re.sub(r'_(.*?)_', r'\1', text)        # Italique alternative
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code inline
        
        # Nettoyer les liens [texte](url) -> texte
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Nettoyer les images ![alt](src) -> alt
        text = re.sub(r'!\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Supprimer les échappements \\
        text = text.replace('\\', '')
        
        #return text.strip()
        
        return text

    def _add_professional_image(self, doc: Document, image_line: str):
        """Ajoute une image avec légende (implémentation basique)"""
        try:
            # Extraction du chemin d'image (format basique: ![alt](path))
            match = re.search(r'!\[.*?\]\((.*?)\)', image_line)
            if match:
                image_path = match.group(1)
                
                # Ajouter une légende
                caption = doc.add_paragraph()
                caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
                caption_run = caption.add_run("Figure: Illustration")
                caption_run.italic = True
                caption_run.font.name = 'Calibri'
                caption_run.font.size = Pt(9)
                caption_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
                
                # Espacement après la légende
                doc.add_paragraph()
                
        except Exception as e:
            logger.warning(f"Erreur ajout image: {e}")

    def _add_professional_headers_footers(self, doc: Document):
        """Ajoute des en-têtes et pieds de page professionnels"""
        try:
            section = doc.sections[0]
            
            # En-tête
            header = section.header
            header_para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            header_para.text = ""
            header_run = header_para.add_run("Document de spécification")
            header_run.font.name = 'Calibri'
            header_run.font.size = Pt(9)
            header_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            
            # Pied de page
            footer = section.footer
            footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            footer_para.text = ""
            
            # Numéro de page à gauche
            footer_run_left = footer_para.add_run()
            footer_run_left.font.name = 'Calibri'
            footer_run_left.font.size = Pt(9)
            
            # Texte central
            footer_run_center = footer_para.add_run(f"Page ")
            footer_run_center.font.name = 'Calibri'
            footer_run_center.font.size = Pt(9)
            
            # Numéro de page
            footer_run_page = footer_para.add_run()
            footer_run_page.font.name = 'Calibri'
            footer_run_page.font.size = Pt(9)
            
            # Date à droite
            footer_run_right = footer_para.add_run(f" • Généré le {datetime.now().strftime('%d/%m/%Y')}")
            footer_run_right.font.name = 'Calibri'
            footer_run_right.font.size = Pt(9)
            footer_run_right.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            
        except Exception as e:
            logger.warning(f"Erreur en-têtes/pieds de page: {e}")

    def _clean_text(self, text: str) -> str:
        """Nettoie le texte pour Word"""
        if not text:
            return ""
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Remplacer les caractères problématiques
        text = text.replace('\u2013', '-').replace('\u2014', '--')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201C', '"').replace('\u201D', '"')
        
        return text.strip()

    
    def _clean_text_keep_unicode(self, text: str) -> str:
        """
        Nettoie le texte tout en conservant les caractères Unicode
        """
        if not text:
            return ""
        
        # Supprimer seulement les caractères de contrôle vraiment dangereux
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normaliser l'Unicode (forme canonique)
        text = unicodedata.normalize('NFC', text)
        
        # Corriger les problèmes d'encodage courants
        text = self._fix_common_encoding_issues(text)
        
        return text.strip()
    

    
    
    def batch_export(self, markdown_content: str, output_base_path: str,
                    formats: List[str] = ['html', 'pdf', 'docx'], 
                    css_path: Optional[str] = None) -> dict:
        """
        Exporte dans multiple formats en une fois
        
        Args:
            markdown_content: Contenu Markdown à convertir
            output_base_path: Chemin de base sans extension
            formats: Liste des formats ['html', 'pdf', 'docx']
            css_path: Chemin vers CSS personnalisé (pour HTML)
        
        Returns:
            dict: Résultats de chaque conversion
        """
        results = {}
        
        # Nettoyer le contenu une seule fois (en conservant Unicode)
        clean_content = self._clean_content_keep_unicode(markdown_content)
        
        if 'html' in formats:
            html_path = f"{output_base_path}.html"
            results['html'] = self.markdown_to_html(clean_content, html_path, css_path)
        
        if 'pdf' in formats:
            pdf_path = f"{output_base_path}.pdf"
            results['pdf'] = self.markdown_to_pdf(clean_content, pdf_path, css_path)
        
        if 'docx' in formats:
            docx_path = f"{output_base_path}.docx"
            results['docx'] = self.markdown_to_docx(clean_content, docx_path)
        
        return results

# Fonction de vérification des dépendances
def check_export_dependencies() -> dict:
    """Vérifie les dépendances d'export disponibles"""
    dependencies = {
        'html': True,  # Toujours disponible avec markdown
        'pdf': False,
        'docx': False
    }
    
    # Vérifier PDF
    try:
        import pdfkit
        dependencies['pdf'] = True
    except ImportError:
        pass
    
    # Vérifier DOCX
    try:
        from docx import Document
        dependencies['docx'] = True
    except ImportError:
        pass
    
    return dependencies

# Utilisation simplifiée
def export_documentation(markdown_file: str, output_dir: str = "exports", 
                        formats: List[str] = None):
    """
    Fonction simplifiée pour exporter la documentation
    
    Args:
        markdown_file: Chemin vers le fichier Markdown
        output_dir: Dossier de sortie pour les exports
        formats: Liste des formats à exporter
    """
    if formats is None:
        formats = ['html', 'pdf', 'docx']
    
    # Vérifier les dépendances disponibles
    available_deps = check_export_dependencies()
    formats = [f for f in formats if available_deps.get(f, False)]
    
    if not formats:
        print("Aucun format d'export disponible. Installez les dépendances:")
        print("  PDF: pip install pdfkit")
        print("  DOCX: pip install python-docx")
        return
    
    # Lire le contenu Markdown
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Créer le dossier d'export
    os.makedirs(output_dir, exist_ok=True)
    
    # Base du nom de fichier
    base_name = os.path.splitext(os.path.basename(markdown_file))[0]
    output_base = os.path.join(output_dir, base_name)
    
    # Exporter
    exporter = DocumentationExporter()
    results = exporter.batch_export(content, output_base, formats)
    
    return results
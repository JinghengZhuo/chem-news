import os
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from chemnews.journal_crawlers import fetch_all_journals
from chemnews.utils import get_config


def send_email(subject, body, attachments, config):
    msg = MIMEMultipart()
    msg['From'] = config['email']
    msg['To'] = config['receiver']
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    for file_path in attachments:
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
            msg.attach(part)

    with smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port']) as server:
        server.login(config['email'], config['password'])
        server.send_message(msg)


def main():
    config = get_config()
    today = datetime.now().strftime('%Y-%m-%d')
    papers = fetch_all_journals()
    # 分类：有机化学优先，其次其他化学领域
    organic_method = []
    organic_material = []
    organic_other = []
    inorganic = []
    analytical = []
    physical = []
    other_chem = []
    attachments = []
    for paper in papers:
        title = paper['title'].lower()
        abstract = paper['abstract'].lower()
        # 有机方法学关键词
        if (('organic' in title or 'organic' in abstract or '有机' in title or '有机' in abstract)):
            if any(k in title or k in abstract for k in ['method', 'synthesis', '合成', '催化', '反应', 'route', 'strategy', '工艺', '转化', '转化率', 'yield', '收率']):
                organic_method.append(paper)
            elif any(k in title or k in abstract for k in ['material', '材料', 'device', '器件', '薄膜', '纳米', '聚合物', 'polymer', '晶体', 'crystal']):
                organic_material.append(paper)
            else:
                organic_other.append(paper)
        elif 'inorganic' in title or 'inorganic' in abstract or '无机' in title or '无机' in abstract:
            inorganic.append(paper)
        elif 'analytical' in title or 'analytical' in abstract or '分析' in title or '分析' in abstract:
            analytical.append(paper)
        elif 'physical' in title or 'physical' in abstract or '物理' in title or '物理' in abstract:
            physical.append(paper)
        elif 'chemistry' in title or 'chemistry' in abstract or '化学' in title or '化学' in abstract:
            other_chem.append(paper)
        # 非化学领域不收录
        # 检查PDF获取情况，若无PDF则查找x-mol分析
        if not paper.get('pdf_path'):
            doi = paper.get('doi', '')
            xmol_info = search_xmol_analysis(doi)
            paper['xmol_info'] = xmol_info
    body = ''
    def paper_block(paper):
        block = f"------------------------------\n标题: {paper['title']}\n作者: {paper['authors']}\n摘要: {paper['abstract']}\n原文链接: {paper['url']}\n"
        if paper.get('pdf_path'):
            attachments.append(paper['pdf_path'])
        else:
            doi = paper.get('doi', '')
            xmol_info = paper.get('xmol_info')
            if xmol_info and xmol_info.get('has_analysis'):
                block += f"未获取到PDF，x-mol分析文章: {xmol_info['title']} (DOI: {xmol_info['doi']})\n分析链接: {xmol_info['url']}\n"
            elif doi:
                block += f"未获取到PDF，DOI: {doi}\n"
            else:
                block += "未获取到PDF，且无DOI信息\n"
        block += '\n'
        return block
    body = ''
    if organic_method:
        body += '【有机方法学】\n'
        for paper in organic_method:
            body += paper_block(paper)
    if organic_material:
        body += '【有机材料】\n'
        for paper in organic_material:
            body += paper_block(paper)
    if organic_other:
        body += '【有机其他】\n'
        for paper in organic_other:
            body += paper_block(paper)
    if inorganic:
        body += '【无机化学】\n'
        for paper in inorganic:
            body += paper_block(paper)
    if analytical:
        body += '【分析化学】\n'
        for paper in analytical:
            body += paper_block(paper)
    if physical:
        body += '【物理化学】\n'
        for paper in physical:
            body += paper_block(paper)
    if other_chem:
        body += '【其他化学】\n'
        for paper in other_chem:
            body += paper_block(paper)
    subject = f"化学期刊最新论文汇总 {today}"
    send_email(subject, body, attachments, config)

# x-mol分析查找函数（需实现实际爬取或API调用）
if __name__ == '__main__':
    main()

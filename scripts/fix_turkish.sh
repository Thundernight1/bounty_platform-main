#!/bin/bash
# Fix Turkish characters in Python files

echo "🔧 Fixing Turkish characters in Python files..."

# reporter.py
sed -i '' 's/# PRE‑REVIEW (Ön Rapor)/# PRE-REVIEW (Pre-Report)/g' bugbounty_7_agents_template/agents/reporter.py
sed -i '' 's/## Özet/## Summary/g' bugbounty_7_agents_template/agents/reporter.py
sed -i '' 's/## İnceleme Notu/## Review Note/g' bugbounty_7_agents_template/agents/reporter.py
sed -i '' 's/Bu aşamada doğruluğu kontrol et ve `outputs\/APPROVED.txt` oluştur./Review findings and create `outputs\/APPROVED.txt` to approve./g' bugbounty_7_agents_template/agents/reporter.py
sed -i '' 's/## Bulgular Özeti/## Findings Summary/g' bugbounty_7_agents_template/agents/reporter.py
sed -i '' 's/Rapor üretildi/Report generated/g' bugbounty_7_agents_template/agents/reporter.py

# tech_fp.py
sed -i '' 's/# güvenli limit/# safe limit/g' bugbounty_7_agents_template/agents/tech_fp.py
sed -i '' 's/URL için header bilgisi alındı/URLs header info retrieved/g' bugbounty_7_agents_template/agents/tech_fp.py

# content.py
sed -i '' 's/# ffuf varsa basit içerik keşfi/# Simple content discovery with ffuf if available/g' bugbounty_7_agents_template/agents/content.py
sed -i '' 's/ffuf çalıştı/ffuf executed/g' bugbounty_7_agents_template/agents/content.py
sed -i '' 's/ffuf bulunamadı, robots.txt listesi oluşturuldu/ffuf not found, robots.txt list created/g' bugbounty_7_agents_template/agents/content.py

# scan_web.py
sed -i '' 's/# httpx + nuclei varsa kullan, yoksa pas geç/# Use httpx + nuclei if available, otherwise skip/g' bugbounty_7_agents_template/agents/scan_web.py
sed -i '' 's/URL üretti/URLs generated/g' bugbounty_7_agents_template/agents/scan_web.py

echo "✅ Done! All Turkish characters replaced with English."

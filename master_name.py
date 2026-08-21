import json

names = ['Aino', 'Albedo', 'Aloy', 'Amber', 'Arataki Itto', 'Arlecchino', 'Barbara', 'Beidou', 'Bennett', 'Candace', 'Charlotte', 'Chasca', 'Chevreuse', 'Chiori', 'Chongyun', 'Citlali', 'Clorinde', 'Columbina', 'Cyno', 'Dahlia', 'Dehya', 'Diluc', 'Diona', 'Dori', 'Durin', 'Escoffier', 'Eula', 'Faruzan', 'Fischl', 'Flins', 'Freminet', 'Furina', 'Gaming', 'Ganyu', 'Gorou', 'Hu Tao', 'Iansan', 'Ifa', 'Illuga', 'Ineffa', 'Jahoda', 'Jean', 'Kachina', 'Kaedehara Kazuha', 'Kaeya', 'Kamisato Ayaka', 'Kamisato Ayato', 'Keqing', 'Klee', 'Kujou Sara', 'Kuki Shinobu', 'Lan Yan', 'Layla', 'Linnea', 'Lisa', 'Lohen', 'Lynette', 'Lyney', 'Mavuika', 'Mika', 'Mona', 'Mualani', 'Navia', 'Neuvillette', 'Nicole', 'Nilou', 'Ningguang', 'Noelle', 'Ororon', 'Prune', 'Qiqi', 'Raiden Shogun', 'Razor', 'Rosaria', 'Sangonomiya Kokomi', 'Sayu', 'Sethos', 'Shenhe', 'Shikanoin Heizou', 'Sigewinne', 'Skirk', 'Sucrose', 'Tartaglia', 'Thoma', 'Varesa', 'Varka', 'Venti', 'Wanderer', 'Wriothesley', 'Xiangling', 'Xianyun', 'Xiao', 'Xilonen', 'Xingqiu', 'Xinyan', 'Yae Miko', 'Yanfei', 'Yelan', 'Yoimiya', 'Yumemizuki Mizuki', 'Yun Jin', 'Zhongli', 'Zibai',
         'Aether', 'Lumine']

with open("character_names.json", "w", encoding="utf-8") as f:
    json.dump(names, f, indent=2)

print(f"Saved {len(names)} names")
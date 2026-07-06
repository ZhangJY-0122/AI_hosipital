import argparse
import copy
import json
from pathlib import Path


TEMPLATES = [
    {
        "department": "内科病例 心血管内科病例",
        "disease": "高血压急症",
        "chief": "{side_note}头痛、头晕伴血压升高{days}天。",
        "symptom": "反复头痛、头晕，活动后加重，伴胸闷，无明显肢体活动障碍。",
        "history": "既往有高血压病史，服药不规律，否认糖尿病及冠心病史。",
        "exam": "血压{bp_high}/{bp_low}mmHg，神志清楚，双肺呼吸音清，心率{pulse}次/分，律齐，双下肢无水肿。",
        "tests": "心电图示窦性心律，部分导联ST-T改变；肾功能未见明显异常。",
        "diagnosis": "高血压3级很高危；高血压急症",
        "treatment": "给予降压、改善循环、监测血压及生活方式干预，病情逐渐稳定。",
    },
    {
        "department": "内科病例 呼吸内科病例",
        "disease": "社区获得性肺炎",
        "chief": "发热、咳嗽、咳痰{days}天。",
        "symptom": "出现发热、咳嗽，咳黄色黏痰，伴乏力，无明显胸痛及咯血。",
        "history": "既往体健，否认结核病史，近期有受凉史。",
        "exam": "体温{temp}℃，脉搏{pulse}次/分，右下肺可闻及湿啰音。",
        "tests": "血常规白细胞及中性粒细胞比例升高；胸部CT提示右下肺炎症。",
        "diagnosis": "社区获得性肺炎",
        "treatment": "给予抗感染、祛痰、补液及对症治疗后体温下降，咳嗽减轻。",
    },
    {
        "department": "内科病例 消化内科病例",
        "disease": "急性胃肠炎",
        "chief": "腹痛、腹泻{days}天。",
        "symptom": "进食不洁食物后出现阵发性腹痛、腹泻，伴恶心，无明显呕血黑便。",
        "history": "既往无慢性胃肠疾病史，否认药物及食物过敏史。",
        "exam": "腹软，脐周轻压痛，无反跳痛，肠鸣音活跃。",
        "tests": "血常规轻度白细胞升高；电解质提示轻度低钾。",
        "diagnosis": "急性胃肠炎；轻度电解质紊乱",
        "treatment": "给予补液、调节肠道菌群、解痉止泻及纠正电解质治疗后好转。",
    },
    {
        "department": "内科病例 神经内科病例",
        "disease": "脑梗死",
        "chief": "{side_note}肢体无力{days}天。",
        "symptom": "突然出现一侧肢体无力，言语略含糊，无明显头痛、呕吐及意识障碍。",
        "history": "既往有高血压及吸烟史，平素血压控制欠佳。",
        "exam": "神志清楚，言语欠流利，{side_note}肢体肌力4级，病理征可疑阳性。",
        "tests": "头颅CT未见出血；头颅MRI提示急性脑梗死灶。",
        "diagnosis": "急性脑梗死；高血压病",
        "treatment": "给予抗血小板聚集、调脂稳斑、改善循环及康复训练，症状较前改善。",
    },
    {
        "department": "内科病例 内分泌科病例",
        "disease": "2型糖尿病",
        "chief": "口干、多饮、多尿{days}天。",
        "symptom": "近来明显口干、多饮、多尿，伴乏力，体重较前下降。",
        "history": "既往血糖偏高未规律治疗，家族中有糖尿病史。",
        "exam": "体型偏胖，皮肤黏膜稍干，双肺及心脏查体未见明显异常。",
        "tests": "空腹血糖{glucose}mmol/L，糖化血红蛋白升高，尿糖阳性。",
        "diagnosis": "2型糖尿病；血糖控制不佳",
        "treatment": "给予饮食运动指导、降糖治疗及血糖监测，症状逐渐缓解。",
    },
    {
        "department": "外科病例 普外科病例",
        "disease": "急性胆囊炎",
        "chief": "右上腹疼痛伴恶心{days}天。",
        "symptom": "进食油腻食物后右上腹持续疼痛，阵发性加重，伴恶心。",
        "history": "既往有胆囊结石病史，未规律复查。",
        "exam": "右上腹压痛，Murphy征阳性，无明显腹肌紧张。",
        "tests": "腹部超声提示胆囊结石并胆囊壁增厚；白细胞升高。",
        "diagnosis": "急性胆囊炎；胆囊结石",
        "treatment": "给予禁食、抗感染、解痉止痛及外科评估，腹痛较前缓解。",
    },
    {
        "department": "内科病例 泌尿内科病例",
        "disease": "急性尿路感染",
        "chief": "尿频、尿急、尿痛{days}天。",
        "symptom": "出现尿频、尿急、尿痛，伴下腹不适，无明显腰痛及寒战。",
        "history": "既往偶有类似症状，饮水较少。",
        "exam": "下腹轻压痛，双肾区叩击痛阴性。",
        "tests": "尿常规白细胞升高，亚硝酸盐阳性；血常规未见明显异常。",
        "diagnosis": "急性下尿路感染",
        "treatment": "给予抗感染、多饮水及对症处理后尿路刺激症状减轻。",
    },
    {
        "department": "内科病例 血液内科病例",
        "disease": "缺铁性贫血",
        "chief": "乏力、头晕{days}周。",
        "symptom": "逐渐出现乏力、头晕，活动后心悸，面色较前苍白。",
        "history": "平素饮食不规律，近期食欲欠佳，否认明显出血史。",
        "exam": "睑结膜苍白，心肺查体未见明显异常，腹部无压痛。",
        "tests": "血红蛋白降低，平均红细胞体积下降，血清铁蛋白降低。",
        "diagnosis": "缺铁性贫血",
        "treatment": "给予补铁、营养支持并查找贫血原因，乏力症状改善。",
    },
    {
        "department": "内科病例 呼吸内科病例",
        "disease": "慢性阻塞性肺疾病急性加重",
        "chief": "咳嗽、咳痰、气促加重{days}天。",
        "symptom": "长期咳嗽咳痰，近日气促加重，活动耐量下降。",
        "history": "长期吸烟史，既往诊断慢性支气管炎。",
        "exam": "桶状胸，双肺呼吸音低，可闻及散在哮鸣音。",
        "tests": "血气分析提示轻度低氧；胸片示肺纹理增多。",
        "diagnosis": "慢性阻塞性肺疾病急性加重",
        "treatment": "给予吸氧、支气管扩张剂、抗感染及祛痰治疗后气促减轻。",
    },
    {
        "department": "内科病例 肾内科病例",
        "disease": "慢性肾脏病",
        "chief": "双下肢水肿{days}周。",
        "symptom": "双下肢水肿逐渐加重，晨起眼睑浮肿，尿量较前减少。",
        "history": "既往有高血压病史多年，血压控制一般。",
        "exam": "血压{bp_high}/{bp_low}mmHg，双下肢凹陷性水肿。",
        "tests": "尿蛋白阳性，血肌酐升高，肾脏超声提示慢性肾实质改变。",
        "diagnosis": "慢性肾脏病；高血压病",
        "treatment": "给予控制血压、利尿消肿、保护肾功能及低盐优质低蛋白饮食指导。",
    },
]


OCCUPATIONS = ["工人", "农民", "教师", "退休人员", "个体经营者", "司机", "公司职员"]
SIDE_NOTES = ["左侧", "右侧"]


def make_record(template: dict, case_id: int, variant: int) -> dict:
    gender = "男" if variant % 2 == 0 else "女"
    age = 35 + (variant * 7 + case_id) % 48
    occupation = OCCUPATIONS[variant % len(OCCUPATIONS)]
    days = 1 + variant % 5
    side_note = SIDE_NOTES[variant % 2]
    bp_high = 145 + variant % 45
    bp_low = 88 + variant % 25
    pulse = 76 + variant % 36
    temp = round(37.3 + (variant % 12) * 0.1, 1)
    glucose = round(7.8 + (variant % 10) * 0.6, 1)

    values = {
        "days": days,
        "side_note": side_note,
        "bp_high": bp_high,
        "bp_low": bp_low,
        "pulse": pulse,
        "temp": temp,
        "glucose": glucose,
    }

    chief = template["chief"].format(**values)
    current_history = template["symptom"]
    past_history = template["history"]
    exam = template["exam"].format(**values)
    tests = template["tests"].format(**values)
    diagnosis = template["diagnosis"]
    treatment = template["treatment"]

    medical_record = {
        "一般资料": f"\n性别: {gender}\n年龄: {age}岁\n职业: {occupation}\n",
        "主诉": f"\n{chief}\n",
        "现病史": f"\n患者{days}天前出现相关不适，主要表现为{current_history} 为进一步诊治来院。\n",
        "既往史": f"\n{past_history} 否认重大手术外伤史，否认明确药物及食物过敏史。\n",
        "查体": f"\n{exam}\n",
        "辅助检查": f"\n{tests}\n",
        "初步诊断": f"\n{diagnosis}\n",
        "诊断依据": f"\n1. 病史及主诉符合{template['disease']}相关表现。\n2. 查体可见相应阳性体征。\n3. 辅助检查结果支持临床判断。\n",
        "鉴别诊断": "\n需与症状相近的急症、感染性疾病及慢性基础病急性加重相鉴别，结合查体和辅助检查进一步排除。\n",
        "诊治经过": f"\n{treatment}\n",
        "诊断结果": f"\n{diagnosis}\n",
        "分析总结": f"\n本例为合成病例，参考既有病例结构生成。患者以{chief}为主要表现，结合病史、查体及辅助检查，考虑{diagnosis}。治疗上以对因治疗、对症处理和随访管理为主。\n",
    }

    profile = (
        f"<病情陈述> 你这几天主要不舒服是{chief}你会用日常语言描述症状，"
        f"比如先说最明显的不舒服，再补充有没有发热、疼痛、乏力等情况。\n"
        f"<性别> {gender}\n"
        f"<年龄> {age}\n"
        f"<工作与生活> 你是一位{occupation}，平时生活节奏普通，对医学术语不太熟悉。\n"
        f"<说法方式> 你回答医生问题时尽量简短真实，不主动说出全部检查结果，除非医生问到。"
    )

    raw_medical_record = {key: value.strip() for key, value in medical_record.items()}
    reformed_text = "\n\n".join(f"#{key}#:{value}" for key, value in medical_record.items())

    return {
        "local": f"合成病例中心 {template['department']} {template['disease']} 样本{variant + 1}",
        "title": f"{template['disease']}合成病例样本{variant + 1}",
        "author": "AI_Hospital synthetic generator",
        "department": template["department"],
        "diseases": template["disease"],
        "time": "生成时间：2026-07-06",
        "read_num": "0",
        "comment_num": "0",
        "url": "",
        "id": case_id,
        "disease_info": None,
        "raw_medical_record": raw_medical_record,
        "reformed_text_medical_record": reformed_text,
        "medical_record": medical_record,
        "profile": profile,
    }


def generate_patients(start_id: int, count: int) -> list[dict]:
    patients = []
    for index in range(count):
        template = TEMPLATES[index % len(TEMPLATES)]
        patients.append(make_record(template, start_id + index, index))
    return patients


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="基于现有病例结构生成合成病例")
    parser.add_argument("--source", type=Path, default=Path("data/patients.json"))
    parser.add_argument("--output", type=Path, default=Path("data/patients_generated_100.json"))
    parser.add_argument("--merged-output", type=Path, default=Path("data/patients_plus_generated_100.json"))
    parser.add_argument("--count", type=int, default=100)
    args = parser.parse_args()

    existing = json.loads(args.source.read_text(encoding="utf-8"))
    max_id = max(int(patient["id"]) for patient in existing)
    generated = generate_patients(max_id + 1, args.count)

    write_json(args.output, generated)
    write_json(args.merged_output, existing + generated)
    print(f"Generated {len(generated)} patients: {args.output}")
    print(f"Merged total {len(existing) + len(generated)} patients: {args.merged_output}")


if __name__ == "__main__":
    main()

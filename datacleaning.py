import pandas as pd
from collections import Counter
import math

p108_df = pd.read_csv("query1.csv")
p108_df.rename(columns={"instCountryLabel": "country"}, inplace=True)

for col in ["awardYear", "startYear", "endYear"]:
    if col in p108_df.columns:
        p108_df[col] = pd.to_numeric(p108_df[col], errors="coerce")
        p108_df.loc[p108_df[col] == -1, col] = math.nan

country_map = {
    "German Reich": "Germany",
    "Nazi Germany": "Germany",
    "Kingdom of Württemberg": "Germany",
    "Kingdom of Prussia": "Germany",
    "Prussia": "Germany",
    "Holy Roman Empire": "Germany",
    "Kingdom of Italy": "Italy",
    "Faroe Islands": "Denmark",
    "Russian Empire": "Russia",
    "Russian Socialist Federative Soviet Republic": "Russia",
    "Soviet Union": "Russia",
    "People's Republic of China": "China",
    "Republic of China": "China",
    "Manchukuo": "China",
    "Taiwan under Japanese rule": "Taiwan",
    "Romanian People's Republic": "Romania",
}

for col in ["birthCountryLabel", "country"]:
    if col in p108_df.columns:
        p108_df[col] = p108_df[col].replace(country_map)

records = []

groups = p108_df.groupby(["laureateName", "awardYear"], group_keys=False)

for (laureate, award_year), group in groups:
    award_year = int(award_year)
    birth_country = group["birthCountryLabel"].iloc[0]

    institutions = []
    for _, row in group.iterrows():
        institutions.append({
            "country": row["country"],
            "start_year": row["startYear"],
            "end_year": row["endYear"]
        })
    overlapping = []
    for inst in institutions:
        s = inst["start_year"]
        e = inst["end_year"]

        if pd.isna(s):
            s = -9999
        if pd.isna(e):
            e = 9999

        if s <= award_year <= e:
            overlapping.append(inst)

    chosen_country = None

    if overlapping:
        with_time = [i for i in overlapping if not (pd.isna(i["start_year"]) and pd.isna(i["end_year"]))]
        candidates = with_time if with_time else overlapping

        def inst_key(inst):
            s, e = inst["start_year"], inst["end_year"]
            if pd.isna(s) or pd.isna(e):
                duration = 0
            else:
                duration = max(0, e - s)

            if pd.isna(s):
                s = award_year
            if pd.isna(e):
                e = award_year
            mid = (s + e) / 2
            dist = abs(mid - award_year)
            return (-duration, dist)

        candidates.sort(key=inst_key)
        chosen_country = candidates[0]["country"]

    else:
        with_time = []
        for inst in institutions:
            s = inst["start_year"]
            e = inst["end_year"]
            if not (pd.isna(s) and pd.isna(e)):
                with_time.append(inst)

        if with_time:
            def inst_key2(inst):
                s, e = inst["start_year"], inst["end_year"]
                if pd.isna(s) or pd.isna(e):
                    duration = 0
                else:
                    duration = max(0, e - s)

                if pd.isna(s):
                    s = award_year
                if pd.isna(e):
                    e = award_year
                mid = (s + e) / 2
                dist = abs(mid - award_year)
                return (-duration, dist)

            with_time.sort(key=inst_key2)
            chosen_country = with_time[0]["country"]

        else:
            countries = [inst["country"] for inst in institutions if inst["country"]]
            if countries:
                chosen_country = Counter(countries).most_common(1)[0][0]

    records.append({
        "laureateName": laureate,
        "awardYear": award_year,
        "birthCountryLabel": birth_country,
        "mainResearchCountry": chosen_country
    })

df_clean = pd.DataFrame(records)

total_records = len(df_clean)
total_laureates = df_clean["laureateName"].nunique()
complete_cases = df_clean.dropna(subset=["birthCountryLabel", "mainResearchCountry"]).shape[0]
migration_cases = (df_clean["birthCountryLabel"] != df_clean["mainResearchCountry"]).sum()
migration_rate = migration_cases / total_records if total_records > 0 else math.nan
time_min = int(df_clean["awardYear"].min())
time_max = int(df_clean["awardYear"].max())

all_countries = pd.unique(pd.concat([df_clean["birthCountryLabel"], df_clean["mainResearchCountry"]]))
n_countries = len(all_countries)

if __name__ == "__main__":
    print("AFTER MAPPING SUMMARY")
    print(f"- Total records (laureate × award): {total_records}")
    print(f"- Total unique laureates: {total_laureates}")
    print(f"- Time span: {time_min}–{time_max}")
    print(f"- Countries represented after mapping: {n_countries}")
    print(f"- Complete cases: {complete_cases}")

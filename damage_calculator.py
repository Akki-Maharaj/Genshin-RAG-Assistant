
from dataclasses import dataclass, field
from typing import Optional



@dataclass
class StatBuckets:
    atk_flat: float = 0.0
    atk_percent: float = 0.0

    hp_flat: float = 0.0
    hp_percent: float = 0.0
    def_flat: float = 0.0
    def_percent: float = 0.0

    em_flat: float = 0.0

    er_percent: float = 0.0

    crit_rate_percent: float = 0.0
    crit_dmg_percent: float = 0.0

    dmg_percent: float = 0.0

    reaction_multiplier: float = 0.0

    enemy_res_percent: float = 10.0
    enemy_def_reduction_percent: float = 0.0

    def add(self, other: "StatBuckets") -> "StatBuckets":
        result = StatBuckets(**self.__dict__)
        for key in self.__dict__:
            if key in ("enemy_res_percent",):
                continue
            setattr(result, key, getattr(result, key) + getattr(other, key))
        return result


@dataclass
class BonusSource:
    name: str
    buckets: StatBuckets



@dataclass
class CharacterBuild:
    character_name: str
    level: int
    base_hp: float
    base_atk: float
    base_def: float
    weapon_base_atk: float
    talent_multiplier: float
    talent_scaling_stat: str = "ATK"

    sources: list = field(default_factory=list)

    def add_source(self, name: str, **bucket_kwargs):
        self.sources.append(BonusSource(name, StatBuckets(**bucket_kwargs)))

    def total_buckets(self) -> StatBuckets:
        total = StatBuckets()
        for s in self.sources:
            total = total.add(s.buckets)
        return total



def calculate_damage(build: CharacterBuild, is_crit: Optional[bool] = None) -> dict:
    b = build.total_buckets()

    if build.talent_scaling_stat == "ATK":
        base_stat = build.base_atk + build.weapon_base_atk
        total_stat = base_stat * (1 + b.atk_percent / 100) + b.atk_flat
    elif build.talent_scaling_stat == "HP":
        base_stat = build.base_hp
        total_stat = base_stat * (1 + b.hp_percent / 100) + b.hp_flat
    elif build.talent_scaling_stat == "DEF":
        base_stat = build.base_def
        total_stat = base_stat * (1 + b.def_percent / 100) + b.def_flat
    else:
        raise ValueError(f"Unknown talent_scaling_stat: {build.talent_scaling_stat}")

    base_damage = total_stat * build.talent_multiplier

    dmg_multiplier = 1 + (b.dmg_percent / 100)

    reaction_multiplier = 1 + b.reaction_multiplier

    res_multiplier = 1 - (b.enemy_res_percent / 100)
    def_multiplier = 1 - (b.enemy_def_reduction_percent / 100)
    def_multiplier = max(def_multiplier, 0.1)

    non_crit_damage = base_damage * dmg_multiplier * reaction_multiplier * res_multiplier * def_multiplier

    crit_rate = max(0, min(100, 5.0 + b.crit_rate_percent))
    crit_dmg = 50.0 + b.crit_dmg_percent
    crit_damage = non_crit_damage * (1 + crit_dmg / 100)

    expected_damage = non_crit_damage * (1 + (crit_rate / 100) * (crit_dmg / 100))

    if is_crit is True:
        final = crit_damage
    elif is_crit is False:
        final = non_crit_damage
    else:
        final = expected_damage

    return {
        "final_damage": round(final, 1),
        "non_crit_damage": round(non_crit_damage, 1),
        "crit_damage": round(crit_damage, 1),
        "expected_damage": round(expected_damage, 1),
        "total_scaling_stat": round(total_stat, 1),
        "base_damage_before_multipliers": round(base_damage, 1),
        "crit_rate_percent": round(crit_rate, 1),
        "crit_dmg_percent": round(crit_dmg, 1),
        "dmg_bonus_percent": round(b.dmg_percent, 1),
        "sources_applied": [s.name for s in build.sources],
    }



if __name__ == "__main__":
    build = CharacterBuild(
        character_name="Example Character",
        level=90,
        base_hp=14000,
        base_atk=280,
        base_def=800,
        weapon_base_atk=608,
        talent_multiplier=2.50,
        talent_scaling_stat="ATK",
    )

    build.add_source("Weapon passive (crit dmg)", crit_dmg_percent=66.0)
    build.add_source("Artifact set 4pc", dmg_percent=15.0)
    build.add_source("Artifact substats", atk_percent=46.6, crit_rate_percent=31.2, crit_dmg_percent=62.4)
    build.add_source("Team buff (e.g. Bennett)", atk_percent=20.0)

    result = calculate_damage(build)
    for k, v in result.items():
        print(f"{k}: {v}")

"""俄语形态服务广覆盖抽检：变位、变格、体配对与回归断言。"""
from __future__ import annotations

import unittest
from typing import Any, Dict, List, Optional

from app.services.morph_service import MorphologyService


def _pres_actv_1sg(service: MorphologyService, word: str) -> Optional[str]:
    r: Dict[str, Any] = service.build_verb_conjugation(word)
    for c in r["cells"]:
        if (
            c.get("type") == "conjugation"
            and c.get("tense") == "pres"
            and c.get("voice") == "actv"
            and c.get("person") == "1per"
            and c.get("number") == "sing"
        ):
            return c.get("form")
    return None


def _pres_1sg_any_voice(service: MorphologyService, word: str) -> Optional[str]:
    """现在时第一人称单数（主动或反身），用于 учиться 等。"""
    r = service.build_verb_conjugation(word)
    for c in r["cells"]:
        if (
            c.get("type") == "conjugation"
            and c.get("tense") == "pres"
            and c.get("person") == "1per"
            and c.get("number") == "sing"
            and c.get("voice") in ("actv", "rfle")
        ):
            f = c.get("form")
            if f:
                return str(f)
    return None


def _futr_actv_1sg(service: MorphologyService, word: str) -> Optional[str]:
    r = service.build_verb_conjugation(word)
    for c in r["cells"]:
        if (
            c.get("type") == "conjugation"
            and c.get("tense") == "futr"
            and c.get("voice") == "actv"
            and c.get("person") == "1per"
            and c.get("number") == "sing"
        ):
            return c.get("form")
    return None


def _aspect_pair_for_lemma(service: MorphologyService, word: str, lemma: str) -> Optional[Dict[str, Any]]:
    r: Dict[str, Any] = service.analyze_root_and_aspect(word)
    for item in r["root_analysis"]:
        if item.get("normal_form") == lemma:
            return item.get("aspect_pair")
    return None


def _declension_nomn_sing(service: MorphologyService, word: str) -> Optional[str]:
    r: Dict[str, Any] = service.build_declension(word)
    for c in r["cells"]:
        if c.get("case") == "nomn" and c.get("number") == "sing":
            return c.get("form")
    return None


def _pres_actv_participle_nomn_forms(service: MorphologyService, word: str) -> List[str]:
    r: Dict[str, Any] = service.build_verb_conjugation(word)
    out: List[str] = []
    for c in r["cells"]:
        if (
            c.get("type") == "participle"
            and c.get("tense") == "pres"
            and c.get("voice") == "actv"
            and c.get("case") == "nomn"
            and c.get("number") == "sing"
            and c.get("gender") == "masc"
        ):
            f = c.get("form")
            if f:
                out.append(str(f))
    return out


class RuMorphBroadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.svc = MorphologyService("ru")

    def test_metat_present_not_metit_paradigm(self) -> None:
        self.assertEqual(_pres_actv_1sg(self.svc, "метать"), "метаю")
        self.assertEqual(_pres_actv_1sg(self.svc, "метить"), "мечу")

    def test_metat_declension_nomn_not_mechuschiy(self) -> None:
        self.assertEqual(_declension_nomn_sing(self.svc, "метать"), "метающий")

    def test_metat_participle_no_duplicate_mechuschiy(self) -> None:
        masc_nomn = _pres_actv_participle_nomn_forms(self.svc, "метать")
        self.assertIn("метающий", masc_nomn)
        self.assertNotIn("мечущий", masc_nomn)

    def test_pomogat_aspect_pair_pomoch_not_popomogat(self) -> None:
        pair = _aspect_pair_for_lemma(self.svc, "помогать", "помогать")
        self.assertIsNotNone(pair)
        assert pair is not None
        self.assertEqual(pair.get("aspect"), "perf")
        self.assertEqual(pair.get("word"), "помочь")

    def test_pomoch_aspect_pair_pomogat(self) -> None:
        pair = _aspect_pair_for_lemma(self.svc, "помочь", "помочь")
        self.assertIsNotNone(pair)
        assert pair is not None
        self.assertEqual(pair.get("aspect"), "impf")
        self.assertEqual(pair.get("word"), "помогать")

    def test_prefix_aspect_pair_delat_sdelat(self) -> None:
        pair = _aspect_pair_for_lemma(self.svc, "делать", "делать")
        self.assertIsNotNone(pair)
        assert pair is not None
        self.assertEqual(pair.get("aspect"), "perf")
        self.assertEqual(pair.get("word"), "сделать")

    def test_kapat_conjugation_stable(self) -> None:
        self.assertEqual(_pres_actv_1sg(self.svc, "капать"), "капаю")

    def test_common_verbs_present(self) -> None:
        samples = [
            ("читать", "читаю"),
            ("писать", "пишу"),
            ("говорить", "говорю"),
            ("мочь", "могу"),
            ("ехать", "еду"),
            ("пить", "пью"),
        ]
        for w, expected in samples:
            with self.subTest(word=w):
                self.assertEqual(_pres_actv_1sg(self.svc, w), expected)

    def test_noun_plural_override_stul(self) -> None:
        r = self.svc.build_declension("стул")
        plur_nomn = next(
            (c["form"] for c in r["cells"] if c.get("case") == "nomn" and c.get("number") == "plur"),
            None,
        )
        self.assertEqual(plur_nomn, "стулья")

    def test_noun_declension_dom(self) -> None:
        r = self.svc.build_declension("дом")
        self.assertEqual(r.get("normal_form"), "дом")
        gent_sing = next(
            (c["form"] for c in r["cells"] if c.get("case") == "gent" and c.get("number") == "sing"),
            None,
        )
        self.assertEqual(gent_sing, "дома")

    def test_adjective_nominative_masc(self) -> None:
        r = self.svc.build_adjective_declension("хороший")
        self.assertEqual(r.get("normal_form"), "хороший")
        nomn = next(
            (
                c["form"]
                for c in r["cells"]
                if c.get("case") == "nomn" and c.get("number") == "sing" and c.get("gender") == "masc"
            ),
            None,
        )
        self.assertEqual(nomn, "хороший")

    def test_reflexive_verb_present(self) -> None:
        self.assertEqual(_pres_1sg_any_voice(self.svc, "учиться"), "учусь")

    def test_perfective_verb_future_synthetic(self) -> None:
        """完成体无现在时变位，服务用将来时槽位给出 сделаю。"""
        self.assertIsNone(_pres_actv_1sg(self.svc, "сделать"))
        self.assertEqual(_futr_actv_1sg(self.svc, "сделать"), "сделаю")

    def test_more_nouns_gent_sing(self) -> None:
        pairs = [
            ("книга", "книги"),
            ("окно", "окна"),
            ("мать", "матери"),
            ("дочь", "дочери"),
            ("время", "времени"),
        ]
        for word, expected_gent in pairs:
            with self.subTest(word=word):
                r = self.svc.build_declension(word)
                gent = next(
                    (c["form"] for c in r["cells"] if c.get("case") == "gent" and c.get("number") == "sing"),
                    None,
                )
                self.assertEqual(gent, expected_gent)

    def test_drug_plural_override(self) -> None:
        r = self.svc.build_declension("друг")
        plur_nomn = next(
            (c["form"] for c in r["cells"] if c.get("case") == "nomn" and c.get("number") == "plur"),
            None,
        )
        self.assertEqual(plur_nomn, "друзья")

    def test_analyze_returns_parses(self) -> None:
        r = self.svc.analyze("бежать", limit=3)
        self.assertEqual(r.get("input"), "бежать")
        self.assertGreaterEqual(len(r.get("parses", [])), 1)

    def test_metit_participle_not_metat_paradigm(self) -> None:
        """метить 的现在时主动形动词词干与 метать 的 мета- 不同；勿出现 метающий。"""
        forms = _pres_actv_participle_nomn_forms(self.svc, "метить")
        self.assertIn("метящий", forms)
        self.assertNotIn("метающий", forms)

    def test_past_masc_sing_batch(self) -> None:
        def past_masc(word: str) -> Optional[str]:
            r = self.svc.build_verb_conjugation(word)
            for c in r["cells"]:
                if (
                    c.get("type") == "conjugation"
                    and c.get("tense") == "past"
                    and c.get("number") == "sing"
                    and c.get("gender") == "masc"
                    and c.get("voice") == "actv"
                ):
                    return c.get("form")
            return None

        pairs = [
            ("читать", "читал"),
            ("писать", "писал"),
            ("метать", "метал"),
            ("идти", "шёл"),
        ]
        for w, exp in pairs:
            with self.subTest(word=w):
                self.assertEqual(past_masc(w), exp)

    def test_uk_morphology_smoke(self) -> None:
        uk = MorphologyService("uk")
        r = uk.build_declension("дім")
        self.assertTrue(any(c.get("form") for c in r.get("cells", [])))


if __name__ == "__main__":
    unittest.main()

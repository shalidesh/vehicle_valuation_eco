"""
Fuzzy matching logic for mapping ERP vehicle model names to database model names.
"""
import re
from collections import defaultdict
from typing import List, Tuple, Optional, Set


def normalize_model_text(text: str) -> str:
    if not text or text == 'nan':
        return ''
    text = text.upper().strip()
    substitutions = {'SERIES': '', 'TYPE': '', '-': '', '_': '', '/': ' ', '.': ''}
    for old, new in substitutions.items():
        text = text.replace(old, new)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text: str) -> List[str]:
    if not text or text == 'nan':
        return []
    normalized = normalize_model_text(text)
    return re.findall(r'[A-Z0-9]+', normalized)


def generate_variants(token: str) -> Set[str]:
    variants = {token}
    match_num_letters = re.match(r'^(\d+)([A-Z]+)$', token)
    if match_num_letters:
        num, letters = match_num_letters.groups()
        variants.add(num)
        for i in range(1, len(letters) + 1):
            variants.add(num + letters[:i])
            variants.add(letters[:i] + num)
    match_letters_num = re.match(r'^([A-Z]+)(\d+)$', token)
    if match_letters_num:
        letters, num = match_letters_num.groups()
        variants.add(num)
        variants.add(num + letters)
        for i in range(1, len(letters) + 1):
            variants.add(letters[:i] + num)
    numbers = re.findall(r'\d+', token)
    letters_only = re.sub(r'\d+', '', token)
    if numbers and letters_only:
        for num in numbers:
            variants.add(num)
            variants.add(num + letters_only)
            variants.add(letters_only + num)
    return variants


_CODE_RE = re.compile(r'^([0-9]+[A-Z]{1,3}|[A-Z]{1,3}[0-9]+)$')
_ALWAYS_NOISE = {'LH', 'RH', 'STD', 'OPT', 'LHD', 'RHD', 'AUTO', 'MANUAL', 'MT', 'AT', 'CVT', 'DCT'}


def clean_erp_tokens(tokens: List[str], db_vocab: set, db_vocab_variants: set) -> List[str]:
    out = []
    seen = set()
    for t in tokens:
        t = t.upper()
        if t in seen: continue
        t_variants = generate_variants(t)
        has_variant_in_db = bool(t_variants & db_vocab_variants)
        if t in db_vocab or has_variant_in_db:
            out.append(t)
            seen.add(t)
        elif t in _ALWAYS_NOISE:
            continue
        elif t.isdigit():
            if len(t) >= 2:
                out.append(t)
                seen.add(t)
        elif _CODE_RE.match(t) and not has_variant_in_db:
            continue
        elif len(t) <= 1:
            continue
        else:
            out.append(t)
            seen.add(t)
    return out


def build_db_vocab(db_entries: List[Tuple[str, str]]) -> tuple[set, set]:
    """
    Build vocabulary from all DB model tokens.
    Returns: (vocab, vocab_with_variants)
    """
    vocab = set()
    vocab_with_variants = set()
    for _, model in db_entries:
        tokens = tokenize(model)
        vocab.update(tokens)
        for token in tokens:
            vocab_with_variants.update(generate_variants(token))
    return vocab, vocab_with_variants


def _fuzzy_match_score(token1: str, token2: str) -> float:
    if token1 == token2: return 1.0
    variants1, variants2 = generate_variants(token1), generate_variants(token2)
    overlap = variants1 & variants2
    if overlap:
        max_len = max(len(token1), len(token2))
        min_len = min(len(token1), len(token2))
        return 0.7 + (0.3 * min_len / max_len)
    if token1 in token2 or token2 in token1:
        if len(token1) >= 3 and len(token2) >= 3:
            return min(len(token1), len(token2)) / max(len(token1), len(token2)) * 0.6
    return 0.0


def _coverage(erp_tokens, db_tokens):
    if not db_tokens: return 0.0
    matched = 0.0
    for db_tok in db_tokens:
        best_match = max([_fuzzy_match_score(erp_tok, db_tok) for erp_tok in erp_tokens] + [0.0])
        matched += best_match
    return matched / len(db_tokens)


def _precision(erp_tokens, db_tokens):
    if not erp_tokens: return 0.0
    matched = 0.0
    for erp_tok in erp_tokens:
        best_match = max([_fuzzy_match_score(erp_tok, db_tok) for db_tok in db_tokens] + [0.0])
        matched += best_match
    return matched / len(erp_tokens)


def _substring_bonus(erp_tokens, db_tokens):
    best = 0.0
    for dt in db_tokens:
        for et in erp_tokens:
            if dt != et and len(dt) > 2 and len(et) > 2:
                if dt in et or et in dt:
                    best = max(best, (min(len(dt), len(et)) / max(len(dt), len(et))) * 0.10)
    return best


def _order_bonus(erp_tokens, db_tokens):
    if len(erp_tokens) < 2 or len(db_tokens) < 2: return 0.0
    erp_m, db_m = [], []
    for i, et in enumerate(erp_tokens):
        for j, dt in enumerate(db_tokens):
            if _fuzzy_match_score(et, dt) >= 0.7:
                erp_m.append(i); db_m.append(j)
                break
    if len(erp_m) < 2: return 0.0
    order_preserved = all(erp_m[i] < erp_m[i+1] and db_m[i] < db_m[i+1] for i in range(len(erp_m) - 1))
    return 0.05 if order_preserved else 0.0


def score_model(erp_model_text: str, db_model_name: str, db_vocab: set, db_vocab_variants: set) -> float:
    """Calculate match score between ERP and DB model with fuzzy matching."""
    erp_tokens = clean_erp_tokens(tokenize(erp_model_text), db_vocab, db_vocab_variants)
    db_tokens = tokenize(db_model_name)
    if not db_tokens or not erp_tokens: return 0.0

    cov, prec = _coverage(erp_tokens, db_tokens), _precision(erp_tokens, db_tokens)
    sub, order = _substring_bonus(erp_tokens, db_tokens), _order_bonus(erp_tokens, db_tokens)

    len_diff = abs(len(erp_tokens) - len(db_tokens))
    len_bonus = 0.05 if len_diff == 0 else (0.03 if len_diff == 1 else 0.0)

    extra_penalty = min(max(len(erp_tokens) - len(db_tokens), 0) * 0.02, 0.10)

    score = (cov * 0.55 + prec * 0.30 + sub + order + len_bonus - extra_penalty) * 100
    return max(score, 0.0)


class ModelIndex:
    def __init__(self, db_entries: List[Tuple[str, str]]):
        self.db_entries = db_entries
        self.db_vocab, self.db_vocab_variants = build_db_vocab(db_entries)
        self._token_idx = defaultdict(list)
        self._variant_idx = defaultdict(list)
        self._brand_idx = defaultdict(list)

        for i, (brand, model) in enumerate(db_entries):
            tokens = tokenize(model)
            for tok in tokens:
                self._token_idx[tok].append(i)
                for variant in generate_variants(tok):
                    self._variant_idx[variant].append(i)
            self._brand_idx[brand.upper()].append(i)

    def candidates(self, erp_model_text: str, erp_brand: Optional[str]) -> List[Tuple[str, str]]:
        """Get candidate DB entries based on token and variant overlap."""
        erp_toks = tokenize(erp_model_text)
        if not erp_toks:
            return []

        seen = set()
        for t in erp_toks:
            for idx in self._token_idx.get(t, []):
                seen.add(idx)
            for variant in generate_variants(t):
                for idx in self._variant_idx.get(variant, []):
                    seen.add(idx)

        if erp_brand and erp_brand.strip():
            brand_indices = set(self._brand_idx.get(erp_brand.upper(), []))
            if brand_indices:
                seen &= brand_indices

        return [self.db_entries[i] for i in seen]


def match_vehicle_models(
    erp_brand: str,
    erp_model_text: str,
    db_entries: List[Tuple[str, str]],
    threshold: float = 40,
    index: Optional[ModelIndex] = None,
) -> Tuple[Optional[Tuple[str, str]], float, bool]:
    """
    Match ERP model to DB model with fuzzy matching.
    Returns: (best_match, score, is_brand_mismatch)
    """
    db_vocab = index.db_vocab if index else build_db_vocab(db_entries)[0]
    db_vocab_variants = index.db_vocab_variants if index else build_db_vocab(db_entries)[1]

    pool = []
    if index:
        pool = index.candidates(erp_model_text, erp_brand)
        if not pool and erp_brand:
            pool = index.candidates(erp_model_text, None)
    else:
        pool = db_entries

    if not pool:
        return None, 0.0, False

    erp_tokens = clean_erp_tokens(tokenize(erp_model_text), db_vocab, db_vocab_variants)
    candidates = []

    for db_brand, db_model in pool:
        s = score_model(erp_model_text, db_model, db_vocab, db_vocab_variants)
        if s > 0:
            is_mismatch = (erp_brand and erp_brand.upper() != db_brand.upper())
            candidates.append(((db_brand, db_model), s, is_mismatch))

    if not candidates:
        return None, 0.0, False

    def sort_key(item):
        (db_brand, db_model), s, is_mismatch = item
        db_toks = tokenize(db_model)
        matched_count = sum(
            1 for db_tok in db_toks
            if any(_fuzzy_match_score(erp_tok, db_tok) >= 0.7 for erp_tok in erp_tokens)
        )
        brand_match_priority = 0 if is_mismatch else 1
        return (brand_match_priority, round(s, 1), matched_count, -len(db_toks))

    candidates.sort(key=sort_key, reverse=True)
    best_entry, best_score, is_mismatch = candidates[0]

    return (best_entry, round(best_score, 1), is_mismatch) if best_score >= threshold else (None, 0.0, False)

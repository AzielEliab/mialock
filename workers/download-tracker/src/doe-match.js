/**
 * Hosted Doe descriptor matching. Compatibility leads only — never an ID.
 * Mirrors mialock.doe ranking (uncalibrated). Author: Aziel Eliab.
 */
import DOE_NOTICES from "./doe-notices.json";

const FEMALE = new Set(["female", "f", "woman", "girl", "jane", "w"]);
const MALE = new Set(["male", "m", "man", "boy", "john"]);
const WEIGHTS = {
  sex: 22,
  age_band: 20,
  jurisdiction: 16,
  time_window: 14,
  height: 10,
  build: 6,
  scars_marks: 8,
  clothing: 4,
};
const MIN_LEAD = 30;
const MAX_RANK = 84;
const BOUNDARY =
  "Compatibility leads only — never an identification. Doe hit ≠ ID. Rank scores are uncalibrated operational labels, not the probability that the notice is the missing person.";

function norm(v) {
  return String(v || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

function normalizeSex(value, eventClass) {
  const t = norm(value);
  if (FEMALE.has(t)) return "female";
  if (MALE.has(t)) return "male";
  const ev = norm(eventClass);
  if (ev.startsWith("jane_doe")) return "female";
  if (ev.startsWith("john_doe")) return "male";
  return "";
}

function parseBand(value) {
  if (value == null || value === "") return null;
  if (typeof value === "number") return [value, value];
  const text = norm(value).replace("–", "-").replace("to", "-");
  const m = text.match(/(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)/);
  if (m) {
    const lo = Number(m[1]);
    const hi = Number(m[2]);
    return [Math.min(lo, hi), Math.max(lo, hi)];
  }
  const one = text.match(/(\d+(?:\.\d+)?)/);
  return one ? [Number(one[1]), Number(one[1])] : null;
}

function tokens(text) {
  return new Set(norm(text).split(/[^a-z0-9]+/).filter((t) => t.length > 1));
}

function parseDate(value) {
  if (!value) return null;
  const d = new Date(String(value).slice(0, 10));
  return Number.isNaN(d.getTime()) ? null : d;
}

function scoreRange(field, a, b, aLabel, bLabel, weight) {
  if (!a || !b) return { field, subject: aLabel, notice: bLabel, status: "unknown", detail: "missing bound", contribution: 0 };
  const lo = Math.max(a[0], b[0]);
  const hi = Math.min(a[1], b[1]);
  const overlap = Math.max(0, hi - lo);
  const span = Math.min(a[1] - a[0], b[1] - b[0]);
  if (span <= 0) {
    const dist = Math.abs(a[0] - b[0]);
    if (dist <= 2) return { field, subject: aLabel, notice: bLabel, status: "match", detail: `delta=${dist}`, contribution: weight };
    if (dist <= 5) return { field, subject: aLabel, notice: bLabel, status: "soft_match", detail: `delta=${dist}`, contribution: weight * 0.55 };
    return { field, subject: aLabel, notice: bLabel, status: "mismatch", detail: `delta=${dist}`, contribution: 0 };
  }
  const ratio = overlap / span;
  if (ratio >= 0.5) {
    return {
      field,
      subject: aLabel,
      notice: bLabel,
      status: ratio >= 0.85 ? "match" : "soft_match",
      detail: `overlap=${ratio.toFixed(2)}`,
      contribution: weight * Math.min(1, ratio),
    };
  }
  if (ratio > 0) {
    return { field, subject: aLabel, notice: bLabel, status: "soft_match", detail: `overlap=${ratio.toFixed(2)}`, contribution: weight * ratio * 0.5 };
  }
  return { field, subject: aLabel, notice: bLabel, status: "mismatch", detail: "no overlap", contribution: 0 };
}

function scoreTokens(field, a, b, weight) {
  if (!norm(a) || !norm(b)) return { field, subject: a || "", notice: b || "", status: "unknown", detail: "one or both unknown", contribution: 0 };
  const sa = tokens(a);
  const sb = tokens(b);
  if (norm(a) === norm(b)) return { field, subject: a, notice: b, status: "match", detail: "exact", contribution: weight };
  const shared = [...sa].filter((t) => sb.has(t));
  if (shared.length) {
    const ratio = shared.length / Math.max(sa.size, sb.size);
    return { field, subject: a, notice: b, status: "soft_match", detail: `shared=${shared.join(",")}`, contribution: weight * Math.min(1, ratio + 0.25) };
  }
  return { field, subject: a, notice: b, status: "mismatch", detail: "no shared tokens", contribution: 0 };
}

function jurisTokens(code) {
  const raw = norm(code).replace(/_/g, "-");
  return new Set(raw.split(/[^a-z0-9]+/).filter(Boolean));
}

function scoreJuris(s, n) {
  if (!norm(s) || !norm(n)) return { field: "jurisdiction", subject: s, notice: n, status: "unknown", detail: "missing jurisdiction", contribution: 0 };
  const su = norm(s).toUpperCase();
  const nu = norm(n).toUpperCase();
  if (su === nu || su.includes(nu) || nu.includes(su)) {
    return { field: "jurisdiction", subject: s, notice: n, status: "match", detail: "exact or nested", contribution: WEIGHTS.jurisdiction };
  }
  const shared = [...jurisTokens(s)].filter((t) => jurisTokens(n).has(t) && t !== "us" && t !== "usa");
  if (shared.length) {
    return { field: "jurisdiction", subject: s, notice: n, status: "soft_match", detail: `shared=${shared.join(",")}`, contribution: WEIGHTS.jurisdiction * 0.5 };
  }
  return { field: "jurisdiction", subject: s, notice: n, status: "mismatch", detail: "no shared grain", contribution: 0 };
}

function scoreTime(subject, notice) {
  const s0 = parseDate(subject.time_window_from);
  const s1 = parseDate(subject.time_window_to) || s0;
  const n0 = parseDate(notice.time_window_from);
  const n1 = parseDate(notice.time_window_to) || n0;
  const sl = `${subject.time_window_from || ""}..${subject.time_window_to || ""}`;
  const nl = `${notice.time_window_from || ""}..${notice.time_window_to || ""}`;
  if (!s0 || !n0) return { field: "time_window", subject: sl, notice: nl, status: "unknown", detail: "missing window", contribution: 0 };
  const lo = s0 > n0 ? s0 : n0;
  const hi = s1 < n1 ? s1 : n1;
  if (lo <= hi) return { field: "time_window", subject: sl, notice: nl, status: "match", detail: "windows overlap", contribution: WEIGHTS.time_window };
  const gap = Math.round((lo - hi) / 86400000);
  if (gap <= 180) return { field: "time_window", subject: sl, notice: nl, status: "soft_match", detail: `gap_days=${gap}`, contribution: WEIGHTS.time_window * 0.45 };
  return { field: "time_window", subject: sl, notice: nl, status: "mismatch", detail: `gap_days=${gap}`, contribution: 0 };
}

function bandLabel(score) {
  if (score >= 95) return "Near-certain correlation";
  if (score >= 85) return "Probable candidate";
  if (score >= 70) return "Strong candidate";
  if (score >= 50) return "Investigate";
  if (score >= 30) return "Weak candidate";
  return "Noise";
}

function asDescriptor(raw) {
  const d = raw || {};
  return {
    age_band: d.age_band || "",
    sex: d.sex || "",
    height_cm: d.height_cm != null && d.height_cm !== "" ? Number(d.height_cm) : null,
    height_band: d.height_band || "",
    build: d.build || "",
    scars_marks: d.scars_marks || d.distinguishing_marks || "",
    clothing: d.clothing || "",
    time_window_from: d.time_window_from || d.year_from || "",
    time_window_to: d.time_window_to || d.year_to || "",
    jurisdiction: d.jurisdiction || "",
    event_class: d.event_class || "",
    notice_id: d.notice_id || d.pin_id || "",
    label: d.label || "",
    notes: d.notes || "",
  };
}

function scorePair(subject, notice) {
  const sSex = normalizeSex(subject.sex, subject.event_class);
  const nSex = normalizeSex(notice.sex, notice.event_class);
  let hardSex = false;
  let sexField;
  if (!sSex || !nSex) sexField = { field: "sex", subject: sSex, notice: nSex, status: "unknown", detail: "one or both unknown", contribution: 0 };
  else if (sSex === nSex) sexField = { field: "sex", subject: sSex, notice: nSex, status: "match", detail: "exact", contribution: WEIGHTS.sex };
  else {
    hardSex = true;
    sexField = { field: "sex", subject: sSex, notice: nSex, status: "mismatch", detail: "hard demographic conflict", contribution: 0 };
  }
  const fields = [
    sexField,
    scoreRange("age_band", parseBand(subject.age_band), parseBand(notice.age_band), subject.age_band, notice.age_band, WEIGHTS.age_band),
    scoreJuris(subject.jurisdiction, notice.jurisdiction),
    scoreTime(subject, notice),
    scoreRange(
      "height",
      parseBand(subject.height_cm != null ? String(subject.height_cm) : subject.height_band),
      parseBand(notice.height_cm != null ? String(notice.height_cm) : notice.height_band),
      String(subject.height_cm || subject.height_band || ""),
      String(notice.height_cm || notice.height_band || ""),
      WEIGHTS.height,
    ),
    scoreTokens("build", subject.build, notice.build, WEIGHTS.build),
    scoreTokens("scars_marks", subject.scars_marks, notice.scars_marks, WEIGHTS.scars_marks),
    scoreTokens("clothing", subject.clothing, notice.clothing, WEIGHTS.clothing),
  ];
  const raw = fields.reduce((s, f) => s + (f.contribution || 0), 0);
  const denom = Object.values(WEIGHTS).reduce((s, w) => s + w, 0);
  let penalty = 0;
  if (fields.find((f) => f.field === "age_band")?.status === "mismatch") penalty += 18;
  if (hardSex) penalty += 40;
  const score = Math.max(0, Math.min(MAX_RANK, Math.round((100 * (raw - penalty)) / denom * 10) / 10));
  return {
    notice_id: notice.notice_id,
    label: notice.label || notice.notice_id,
    event_class: notice.event_class,
    rank_score: score,
    label_band: bandLabel(score),
    calibration_status: "uncalibrated",
    hard_sex_mismatch: hardSex,
    is_lead: !hardSex && score >= MIN_LEAD,
    fields,
    next_verification:
      "Compare scars/marks / dental / fingerprints through an authorized ME or clearinghouse channel. Notice remains a compatibility lead only. Do not treat this score as ID.",
    jurisdiction: notice.jurisdiction,
    warning: "DO NOT INTERPRET AS CONFIRMED IDENTITY UNTIL VERIFIED. Doe hit ≠ ID.",
  };
}

const DEFAULT_SUBJECT = {
  age_band: "20-30",
  sex: "female",
  height_cm: 165,
  build: "slim",
  scars_marks: "tattoo left wrist",
  clothing: "red jacket",
  time_window_from: "1994-09-02",
  time_window_to: "1995-12-31",
  jurisdiction: "US-IL-COOK",
  label: "Elena Vargas (hosted demo descriptor)",
};

export function hostedDoeMatch(tokens) {
  const subject = asDescriptor({ ...DEFAULT_SUBJECT, ...tokens });
  const extra = Array.isArray(tokens.notices) ? tokens.notices.map(asDescriptor) : [];
  const notices = extra.length ? extra : (DOE_NOTICES.notices || []).map(asDescriptor);
  const scored = notices.map((n) => scorePair(subject, n));
  const leads = scored.filter((r) => r.is_lead).sort((a, b) => b.rank_score - a.rank_score);
  const excluded = scored.filter((r) => !r.is_lead).map((r) => ({
    notice_id: r.notice_id,
    label: r.label,
    event_class: r.event_class,
    rank_score: r.rank_score,
    reason: r.hard_sex_mismatch ? "sex_mismatch" : "below_lead_threshold",
    fields: r.fields,
    warning: r.warning,
  }));
  return {
    hosted: true,
    boundary: BOUNDARY,
    calibration_status: "uncalibrated",
    subject,
    lead_count: leads.length,
    leads,
    excluded,
    warning: "DO NOT INTERPRET AS CONFIRMED IDENTITY UNTIL VERIFIED. Doe hit ≠ ID.",
    local: { command: "python -m mialock doe-match --subject subj-elena-cold-demo" },
  };
}

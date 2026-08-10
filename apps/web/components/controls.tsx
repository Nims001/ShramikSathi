"use client";

// Small bilingual form controls used by the employer form, signup and profile.
// Option lists come from lib/constants as BilingualOption[].

import type { BilingualOption } from "@/lib/constants";
import { useLanguage } from "@/lib/i18n/LanguageContext";

function labelOf(option: BilingualOption, lang: "en" | "ne"): string {
  return lang === "ne" ? option.ne : option.en;
}

export function optionLabel(value: string, options: BilingualOption[], lang: "en" | "ne"): string {
  return labelOf(options.find((o) => o.value === value) ?? { value, en: value, ne: value }, lang);
}

export function FieldLabel({ text, hint }: { text: string; hint?: string }) {
  return (
    <div className="mb-1.5">
      <span className="block text-sm font-medium text-slate-800">{text}</span>
      {hint ? <span className="mt-0.5 block text-xs text-slate-500">{hint}</span> : null}
    </div>
  );
}

const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20";

export function TextField({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  inputMode,
  min,
  max,
  step,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  inputMode?: "text" | "numeric" | "decimal";
  min?: number;
  max?: number;
  step?: number;
  hint?: string;
}) {
  return (
    <label className="block">
      <FieldLabel text={label} hint={hint} />
      <input
        className={inputClass}
        type={type}
        value={value}
        placeholder={placeholder}
        inputMode={inputMode}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

export function SelectField({
  label,
  value,
  onChange,
  options,
  includeEmpty = true,
  emptyLabel,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: BilingualOption[];
  includeEmpty?: boolean;
  emptyLabel?: string;
}) {
  const { lang, t } = useLanguage();
  return (
    <label className="block">
      <FieldLabel text={label} />
      <select
        className={inputClass}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {includeEmpty ? (
          <option value="">{emptyLabel ?? t("option.choose")}</option>
        ) : null}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {labelOf(o, lang)}
          </option>
        ))}
      </select>
    </label>
  );
}

export function ChoiceGroup({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: BilingualOption[];
}) {
  const { lang } = useLanguage();
  return (
    <fieldset className="block">
      <FieldLabel text={label} />
      <div className="flex flex-wrap gap-2">
        {options.map((o) => {
          const selected = value === o.value;
          return (
            <button
              key={o.value}
              type="button"
              onClick={() => onChange(selected ? "" : o.value)}
              aria-pressed={selected}
              className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                selected
                  ? "border-brand-600 bg-brand-50 font-medium text-brand-800"
                  : "border-slate-300 bg-white text-slate-700 active:bg-slate-100"
              }`}
            >
              {labelOf(o, lang)}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

export function YesNoGroup({
  label,
  value,
  onChange,
  includeUnknown = true,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  includeUnknown?: boolean;
  hint?: string;
}) {
  const { t } = useLanguage();
  const options: BilingualOption[] = [
    { value: "yes", en: t("option.yes"), ne: t("option.yes") },
    { value: "no", en: t("option.no"), ne: t("option.no") },
  ];
  if (includeUnknown) {
    options.push({ value: "unknown", en: t("option.unknown"), ne: t("option.unknown") });
  }
  return (
    <div>
      <ChoiceGroup label={label} value={value} onChange={onChange} options={options} />
      {hint ? <p className="mt-1.5 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}

export function CheckboxField({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-start gap-2.5 rounded-lg border border-slate-300 bg-white px-3 py-2.5">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
      />
      <span className="text-sm text-slate-800">{label}</span>
    </label>
  );
}

export function InfoCard({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-2.5 text-sm text-sky-900">
      {text}
    </div>
  );
}

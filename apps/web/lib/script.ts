// Deterministic negotiation-script generator (template-based, no LLM call).
// Used on the results page and clearly labeled as a suggestion, not legal advice.

import type { Violation } from "./types";

export interface ScriptLine {
  en: string;
  ne: string;
}

// Pull the most serious findings (skip info notes) to quote to the employer.
export function buildScript(violations: Violation[]): ScriptLine[] {
  const serious = violations
    .filter((v) => v.severity !== "info")
    .slice(0, 3);

  const bullets = serious.flatMap((v) => [
    {
      en: `${v.section_reference}: ${v.plain_explanation_en}`,
      ne: `${v.section_reference}: ${v.plain_explanation_ne}`,
    },
  ]);

  return [
    {
      en: "Namaste, I wanted to raise something about my working conditions.",
      ne: "नमस्ते, म आफ्नो कामको अवस्थाबारे केही कुरा राख्न चाहन्थेँ।",
    },
    {
      en: "I learned that under The Labour Act, 2017, my working conditions should be:",
      ne: "मैले थाहा पाएँ कि श्रम ऐन, २०७४ अनुसार मेरो कामको अवस्था यस्तो हुनुपर्छ:",
    },
    ...bullets,
    {
      en: "Could we fix this together? I'd like to resolve it with you before taking it further.",
      ne: "के हामी यो मिलाउन सक्छौं? अझ अगाडि नलगी तपाईंसँगै समाधान गर्न चाहन्छु।",
    },
    {
      en: "Thank you for listening.",
      ne: "सुन्नुभएकोमा धन्यवाद।",
    },
  ];
}

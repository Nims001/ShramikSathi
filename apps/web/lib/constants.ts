// Static reference data used by the bilingual forms.
//
// The ethnicity list is the OFFICIAL classification from the National
// Population and Housing Census 2021 (National Statistics Office, Nepal):
// 141 named caste/ethnic groups in the published rank order, plus "Others"
// (the NSO counts 142 categories). Do not edit these names.

export interface BilingualOption {
  value: string;
  en: string;
  ne: string;
}

export interface Province {
  id: string;
  en: string;
  ne: string;
  districts: BilingualOption[];
}

export const PROVINCES: Province[] = [
  {
    id: "koshi",
    en: "Koshi",
    ne: "कोशी",
    districts: [
      { value: "taplejung", en: "Taplejung", ne: "ताप्लेजुङ" },
      { value: "sankhuwasabha", en: "Sankhuwasabha", ne: "सङ्खुवासभा" },
      { value: "solukhumbu", en: "Solukhumbu", ne: "सोलुखुम्बु" },
      { value: "bhojpur", en: "Bhojpur", ne: "भोजपुर" },
      { value: "khotang", en: "Khotang", ne: "खोटाङ" },
      { value: "okhaldhunga", en: "Okhaldhunga", ne: "ओखलढुङ्गा" },
      { value: "udayapur", en: "Udayapur", ne: "उदयपुर" },
      { value: "jhapa", en: "Jhapa", ne: "झापा" },
      { value: "morang", en: "Morang", ne: "मोरङ" },
      { value: "sunsari", en: "Sunsari", ne: "सुनसरी" },
      { value: "dhankuta", en: "Dhankuta", ne: "धनकुटा" },
      { value: "terhathum", en: "Terhathum", ne: "तेह्रथुम" },
      { value: "panchthar", en: "Panchthar", ne: "पाँचथर" },
      { value: "ilam", en: "Ilam", ne: "इलाम" },
    ],
  },
  {
    id: "madhesh",
    en: "Madhesh",
    ne: "मधेश",
    districts: [
      { value: "saptari", en: "Saptari", ne: "सप्तरी" },
      { value: "siraha", en: "Siraha", ne: "सिराहा" },
      { value: "dhanusha", en: "Dhanusha", ne: "धनुषा" },
      { value: "mahottari", en: "Mahottari", ne: "महोत्तरी" },
      { value: "sarlahi", en: "Sarlahi", ne: "सर्लाही" },
      { value: "bara", en: "Bara", ne: "बारा" },
      { value: "parsa", en: "Parsa", ne: "पर्सा" },
      { value: "rautahat", en: "Rautahat", ne: "रौतहट" },
    ],
  },
  {
    id: "bagmati",
    en: "Bagmati",
    ne: "बागमती",
    districts: [
      { value: "dolakha", en: "Dolakha", ne: "दोलखा" },
      { value: "ramechhap", en: "Ramechhap", ne: "रामेछाप" },
      { value: "sindhuli", en: "Sindhuli", ne: "सिन्धुली" },
      { value: "kavrepalanchok", en: "Kavrepalanchok", ne: "काभ्रेपलान्चोक" },
      { value: "sindhupalchok", en: "Sindhupalchok", ne: "सिन्धुपाल्चोक" },
      { value: "rasuwa", en: "Rasuwa", ne: "रसुवा" },
      { value: "nuwakot", en: "Nuwakot", ne: "नुवाकोट" },
      { value: "dhading", en: "Dhading", ne: "धादिङ" },
      { value: "bhaktapur", en: "Bhaktapur", ne: "भक्तपुर" },
      { value: "kathmandu", en: "Kathmandu", ne: "काठमाडौँ" },
      { value: "lalitpur", en: "Lalitpur", ne: "ललितपुर" },
      { value: "chitwan", en: "Chitwan", ne: "चितवन" },
      { value: "makwanpur", en: "Makwanpur", ne: "मकवानपुर" },
    ],
  },
  {
    id: "gandaki",
    en: "Gandaki",
    ne: "गण्डकी",
    districts: [
      { value: "gorkha", en: "Gorkha", ne: "गोरखा" },
      { value: "lamjung", en: "Lamjung", ne: "लमजुङ" },
      { value: "kaski", en: "Kaski", ne: "कास्की" },
      { value: "tanahun", en: "Tanahun", ne: "तनहुँ" },
      { value: "syangja", en: "Syangja", ne: "स्याङ्जा" },
      { value: "manang", en: "Manang", ne: "मनाङ" },
      { value: "mustang", en: "Mustang", ne: "मुस्ताङ" },
      { value: "parbat", en: "Parbat", ne: "पर्वत" },
      { value: "myagdi", en: "Myagdi", ne: "म्याग्दी" },
      { value: "baglung", en: "Baglung", ne: "बागलुङ" },
      { value: "nawalpur", en: "Nawalpur", ne: "नवलपुर" },
    ],
  },
  {
    id: "lumbini",
    en: "Lumbini",
    ne: "लुम्बिनी",
    districts: [
      { value: "rupandehi", en: "Rupandehi", ne: "रुपन्देही" },
      { value: "kapilvastu", en: "Kapilvastu", ne: "कपिलवस्तु" },
      { value: "parasi", en: "Parasi", ne: "परासी" },
      { value: "palpa", en: "Palpa", ne: "पाल्पा" },
      { value: "gulmi", en: "Gulmi", ne: "गुल्मी" },
      { value: "arghakhanchi", en: "Arghakhanchi", ne: "अर्घाखाँची" },
      { value: "banke", en: "Banke", ne: "बाँके" },
      { value: "bardiya", en: "Bardiya", ne: "बर्दिया" },
      { value: "dang", en: "Dang", ne: "दाङ" },
      { value: "rolpa", en: "Rolpa", ne: "रोल्पा" },
      { value: "pyuthan", en: "Pyuthan", ne: "प्युठान" },
      { value: "east_rukum", en: "Rukum East", ne: "पूर्वी रुकुम" },
    ],
  },
  {
    id: "karnali",
    en: "Karnali",
    ne: "कर्णाली",
    districts: [
      { value: "salyan", en: "Salyan", ne: "सल्यान" },
      { value: "surkhet", en: "Surkhet", ne: "सुर्खेत" },
      { value: "dailekh", en: "Dailekh", ne: "दैलेख" },
      { value: "jajarkot", en: "Jajarkot", ne: "जाजरकोट" },
      { value: "dolpa", en: "Dolpa", ne: "डोल्पा" },
      { value: "jumla", en: "Jumla", ne: "जुम्ला" },
      { value: "kalikot", en: "Kalikot", ne: "कालिकोट" },
      { value: "mugu", en: "Mugu", ne: "मुगु" },
      { value: "humla", en: "Humla", ne: "हुम्ला" },
      { value: "west_rukum", en: "Rukum West", ne: "पश्चिमी रुकुम" },
    ],
  },
  {
    id: "sudurpashchim",
    en: "Sudurpashchim",
    ne: "सुदूरपश्चिम",
    districts: [
      { value: "bajura", en: "Bajura", ne: "बाजुरा" },
      { value: "bajhang", en: "Bajhang", ne: "बझाङ" },
      { value: "achham", en: "Achham", ne: "अछाम" },
      { value: "doti", en: "Doti", ne: "डोटी" },
      { value: "kailali", en: "Kailali", ne: "कैलाली" },
      { value: "kanchanpur", en: "Kanchanpur", ne: "कञ्चनपुर" },
      { value: "dadeldhura", en: "Dadeldhura", ne: "डडेल्धुरा" },
      { value: "baitadi", en: "Baitadi", ne: "बैतडी" },
      { value: "darchula", en: "Darchula", ne: "दार्चुला" },
    ],
  },
];

export function districtsFor(provinceId: string): BilingualOption[] {
  return PROVINCES.find((p) => p.id === provinceId)?.districts ?? [];
}

// Official NPHC 2021 caste/ethnicity classification — 142 categories total.
export const ETHNICITIES: string[] = [
  "Chettri",
  "Brahman - Hill",
  "Magar",
  "Tharu",
  "Tamang",
  "Bishwokarma (Kami)",
  "Musalman",
  "Newa (Newar)",
  "Yadav",
  "Rai",
  "Pariyar",
  "Gurung",
  "Thakuri",
  "Mijar (Sarki)",
  "Teli",
  "Yakthung/Limbu",
  "Chamar/Harijan/Ram",
  "Kushwaha",
  "Kurmi",
  "Musahar",
  "Dhanuk",
  "Dusadh/Pasawan/Pasi",
  "Brahman - Tarai",
  "Mallaha",
  "Sanyasi/Dasnami",
  "Kewat",
  "Kanu",
  "Hajam/Thakur",
  "Kalwar",
  "Rajbansi",
  "Sherpa",
  "Kumal",
  "Tatma/Tatwa",
  "Khatwe",
  "Gharti/Bhujel",
  "Majhi",
  "Nuniya",
  "Sundi",
  "Dhobi",
  "Lohar",
  "Bin",
  "Kumhar",
  "Sonar",
  "Chepang/Praja",
  "Ranatharu",
  "Danuwar",
  "Sunuwar",
  "Haluwai",
  "Baraee",
  "Bantar/Sardar",
  "Kahar",
  "Santhal",
  "Baniyan",
  "Kathabaniyan",
  "Badhaee/Badhee",
  "Oraon/Kudukh",
  "Rajput",
  "Amat",
  "Gangai",
  "Lodh",
  "Gaderi/Bhediyar",
  "Ghale",
  "Marwadi",
  "Kayastha",
  "Kulung",
  "Thami",
  "Bhumihar",
  "Rajbhar",
  "Rauniyar",
  "Dhimal",
  "Khawas",
  "Tajpuriya",
  "Kori",
  "Dom",
  "Mali",
  "Darai",
  "Yakkha",
  "Bhote",
  "Bantawa",
  "Rajdhob",
  "Dhunia",
  "Pahari",
  "Bangali",
  "Gondh/Gond",
  "Chamling",
  "Chhantyal/Chhantel",
  "Thakali",
  "Badi",
  "Bote",
  "Hyolmo/Yholmopa",
  "Khatik",
  "Yamphu",
  "Kewarat",
  "Baram/Baramu",
  "Dev",
  "Nachhiring",
  "Gaine",
  "Bahing",
  "Thulung",
  "Jirel",
  "Khaling",
  "Aathpahariya",
  "Dolpo",
  "Sarbaria",
  "Mewahang",
  "Byasi/Sauka",
  "Dura",
  "Meche",
  "Raji",
  "Sampang",
  "Chai/Khulaut",
  "Chumba/Nubri",
  "Pun",
  "Dhankar/Dharikar",
  "Munda",
  "Lepcha",
  "Patharkatt/Kushwadiya",
  "Hayu",
  "Beldar",
  "Halkhor",
  "Natuwa",
  "Loharung",
  "Kamar",
  "Dhandi",
  "Done",
  "Mugal/Mugum",
  "Punjabi/Sikh",
  "Karmarong",
  "Chidimar",
  "Kisan",
  "Lhopa",
  "Kalar",
  "Phree",
  "Koche",
  "Topkegola",
  "Raute",
  "Walung",
  "Lhomi",
  "Surel",
  "Kusunda",
  "Bankariya",
  "Nurang",
  "Others",
];

export const EMPLOYMENT_TYPES: BilingualOption[] = [
  {
    value: "regular",
    en: "Regular employment",
    ne: "नियमित रोजगार",
  },
  {
    value: "work_based",
    en: "Work-based (paid per specific task)",
    ne: "कार्यआधारित (निश्चित काम अनुसार)",
  },
  {
    value: "time_based",
    en: "Time-bound (fixed period)",
    ne: "समयआधारित (निश्चित अवधि)",
  },
  {
    value: "part_time",
    en: "Part-time (35 hours/week or less)",
    ne: "अंशकालिक (हप्तामा ३५ घण्टा वा सोभन्दा कम)",
  },
  {
    value: "casual",
    en: "Casual (7 days or less in a month)",
    ne: "आकस्मिक (महिनामा ७ दिन वा सोभन्दा कम)",
  },
];

export const GENDERS: BilingualOption[] = [
  { value: "male", en: "Male", ne: "पुरुष" },
  { value: "female", en: "Female", ne: "महिला" },
  { value: "other", en: "Other", ne: "अन्य" },
];

export const EDUCATION_LEVELS: BilingualOption[] = [
  { value: "none", en: "No formal education", ne: "औपचारिक शिक्षा नभएको" },
  { value: "primary", en: "Primary", ne: "प्राथमिक" },
  { value: "secondary", en: "Secondary", ne: "माध्यमिक" },
  { value: "higher_secondary", en: "Higher secondary", ne: "उच्च माध्यमिक" },
  { value: "bachelor", en: "Bachelor's or above", ne: "स्नातक वा सोभन्दा माथि" },
];

export const SKILL_LEVELS: BilingualOption[] = [
  { value: "unskilled", en: "Unskilled", ne: "अदक्ष" },
  { value: "semi_skilled", en: "Semi-skilled", ne: "अर्धदक्ष" },
  { value: "skilled", en: "Skilled", ne: "दक्ष" },
  { value: "highly_skilled", en: "Highly skilled", ne: "अतिदक्ष" },
];

export const HIRING_CHANNELS: BilingualOption[] = [
  { value: "direct", en: "Direct with the employer", ne: "रोजगारदातासँग सिधा" },
  { value: "contractor", en: "Through a labor contractor / manpower agency", ne: "श्रम ठेकेदार / म्यानपावर एजेन्सीबाट" },
  { value: "friend", en: "Through friends or relatives", ne: "साथीभाइ वा नातेदारबाट" },
  { value: "agent", en: "Through an employment agent", ne: "रोजगार एजेन्टबाट" },
  { value: "other", en: "Other", ne: "अन्य" },
];

export const PAY_UNITS: BilingualOption[] = [
  { value: "hourly", en: "Per hour", ne: "प्रति घण्टा" },
  { value: "daily", en: "Per day", ne: "प्रति दिन" },
  { value: "weekly", en: "Per week", ne: "प्रति हप्ता" },
  { value: "monthly", en: "Per month", ne: "प्रति महिना" },
  { value: "per_piece", en: "Per piece / task", ne: "टुक्रा / काम अनुसार" },
];

export const PAY_FREQUENCIES: BilingualOption[] = [
  { value: "daily", en: "Daily", ne: "दैनिक" },
  { value: "weekly", en: "Weekly", ne: "साप्ताहिक" },
  { value: "monthly", en: "Monthly", ne: "मासिक" },
];

export const OVERTIME_RATES: BilingualOption[] = [
  { value: "100", en: "100% (1 × normal pay)", ne: "१००% (सामान्य ज्यालाको १ गुणा)" },
  { value: "150", en: "150% (1.5 × normal pay)", ne: "१५०% (सामान्य ज्यालाको १.५ गुणा)" },
  { value: "other", en: "Other / don't know", ne: "अन्य / थाहा छैन" },
];

export const OVERTIME_UNITS: BilingualOption[] = [
  { value: "day", en: "Per day", ne: "प्रति दिन" },
  { value: "week", en: "Per week", ne: "प्रति हप्ता" },
  { value: "month", en: "Per month", ne: "प्रति महिना" },
  { value: "dont_know", en: "Don't know", ne: "थाहा छैन" },
];

export const OVERTIME_CONSENT: BilingualOption[] = [
  { value: "forced", en: "Forced / cannot refuse", ne: "जबरजस्ती / अस्वीकार गर्न नसकिने" },
  { value: "voluntary", en: "Voluntary / agreed", ne: "स्वेच्छिक / सहमत" },
  { value: "dont_know", en: "Don't know", ne: "थाहा छैन" },
];

export const PAYMENT_METHODS: BilingualOption[] = [
  { value: "cash", en: "Cash", ne: "नगद" },
  { value: "bank", en: "Bank transfer", ne: "बैंक ट्रान्सफर" },
  { value: "wallet", en: "Mobile wallet", ne: "मोबाइल वालेट" },
  { value: "cheque", en: "Cheque", ne: "चेक" },
  { value: "mixed", en: "Mixed", ne: "मिश्रित" },
];

export const WEEKDAYS: BilingualOption[] = [
  { value: "0", en: "Sunday", ne: "आइतबार" },
  { value: "1", en: "Monday", ne: "सोमबार" },
  { value: "2", en: "Tuesday", ne: "मङ्गलबार" },
  { value: "3", en: "Wednesday", ne: "बुधबार" },
  { value: "4", en: "Thursday", ne: "बिहीबार" },
  { value: "5", en: "Friday", ne: "शुक्रबार" },
  { value: "6", en: "Saturday", ne: "शनिबार" },
];

const messages = {
  header: {
    appName: 'Farmer Battle',
    tagline: 'Építs. Képezz. Hódíts.',
    languageLabel: 'Nyelv',
    languages: {
      en: 'Angol',
      hu: 'Magyar',
    },
    roleCommander: 'Parancsnok',
    signOut: 'Kijelentkezés',
    signIn: 'Bejelentkezés',
    createAccount: 'Fiók létrehozása',
  },
  nav: {
    home: 'Kezdőlap',
    village: 'Saját falu',
    leaderboard: 'Ranglista',
    info: 'Információk',
    admin: 'Admin',
  },
  common: {
    duration: {
      soon: 'Hamarosan',
      done: 'Kész',
      hoursMinutes: '{hours} ó {minutes} p',
      minutesSeconds: '{minutes} p {seconds} mp',
      seconds: '{seconds} mp',
      anyMoment: 'bármelyik pillanatban',
      inDuration: '{duration} múlva',
      instant: 'Azonnali',
    },
    notifications: {
      noActiveVillage: 'Nincs kiválasztott aktív falu.',
    },
    errors: {
      noActiveVillage: 'Nincs elérhető aktív falu.',
      loadFailed: 'Nem sikerült betölteni az adatokat.',
      upgradeFailed: 'Nem sikerült elindítani ezt a fejlesztést.',
    },
    levelShort: '{level}. szint',
    quantity: '{value}×',
    unknown: 'Ismeretlen',
  },
  components: {
    buildingDetail: {
      levelHeading: 'Szint',
      effectsHeading: 'Hatások',
      requirementsHeading: 'Követelmények',
      unlocksHeading: 'Feloldások',
      detailsHeading: 'Fejlesztési adatok',
      duration: 'Időtartam: {duration}',
      readyIn: 'Kész {duration} múlva',
      queueing: 'Sorban áll',
      cost: 'Költség: {wood} {woodLabel} · {clay} {clayLabel} · {iron} {ironLabel}',
      levelShort: '{level}. szint',
      requirementMet: 'Kész',
      messages: {
        maxLevel: 'Elérted a maximális szintet.',
        requirementsMissing: 'Hiányzó követelmények a következő fejlesztéshez.',
        notEnoughResources: 'Nincs elég erőforrás a fejlesztéshez.',
      },
      button: {
        maxLevel: 'Elérted a maximális szintet',
        inProgress: 'Fejlesztés folyamatban',
        requirementsMissing: 'Hiányzó követelmények',
        notEnoughResources: 'Kevés erőforrás',
        upgrade: 'Fejlesztés a {level}. szintre',
      },
    },
    resourceCard: {
      perHour: '/óra',
      max: 'Maximum: {value}',
    },
  },
  info: {
    hero: {
      badge: 'Építő kézikönyv',
      title: 'Tervezd meg az utat egy virágzó királyság felé',
      description:
        'Minden felhúzott épület új lehetőségeket nyit meg. Használd ezt az útmutatót, hogy megértsd az épületek kölcsönhatásait, mely fejlesztések nyitják meg az új egységeket vagy technológiákat, és hogyan priorizáld a fejlődési tervedet.',
    },
    loading: 'Épülettervek összegyűjtése...',
    errors: {
      load: 'Most nem sikerült betölteni az építési kézikönyvet. Próbáld újra később.',
    },
    groupCount: {
      single: '{count} épület',
      multi: '{count} épület',
    },
    levelProgress: 'Szint {level}/{max}',
    labels: {
      effectsOnUpgrade: 'Fejlesztés hatása',
    },
    requirements: {
      none: 'Nincs előfeltétel',
    },
    dependency: {
      heading: 'Függőségi fák',
      description:
        'Kövesd az ágakat, hogy lásd, mely épületek nyitják meg a következő szintet. A jelvényeken szereplő követelményeknek is teljesülniük kell.',
      standaloneTag: 'Önálló',
      empty: 'Ehhez az épülethez nem tartoznak további feloldások.',
    },
  },
  village: {
    header: {
      title: 'Falu áttekintés',
      subtitle: 'Üdv újra, Parancsnok!',
      playerName: 'Játékos neve',
      playerLevel: '1. szint',
      avatarLabel: 'Játékos avatárja',
    },
    sections: {
      resources: 'Erőforrások',
      buildings: 'Épületek',
      military: 'Katonai helyzet',
    },
    resources: {
      gold: { title: 'Arany', subtitle: 'Kincstár' },
      wood: { title: 'Fa', subtitle: 'Nyersanyag' },
      clay: { title: 'Agyag', subtitle: 'Nyersanyag' },
      iron: { title: 'Vas', subtitle: 'Nyersanyag' },
    },
    buildingQueue: {
      title: 'Építési sor',
      count: '{count} aktív',
      empty: 'Jelenleg nincs folyamatban fejlesztés. Adj munkát az építőidnek!',
      finishesAt: 'Befejezés ideje',
    },
    notifications: {
      creatingVillage: 'Nem találtuk a falut, létrehozunk egyet...',
      created: 'Új falu létrehozva!',
      createError: 'Hiba történt a falu létrehozásakor!',
      fetchFailed: 'Nem sikerült lekérni a falu adatait.',
      upgradeError: 'Hiba történt a(z) {building} fejlesztésekor.',
      ensureActiveFailed: 'Nem sikerült betölteni az aktív falut.',
      upgradeStartedCustom: '{building} fejlesztése elindult!',
    },
    military: {
      readyTroops: {
        title: 'Kész egységek',
        loading: 'Egységek betöltése...',
        empty: 'Nincsenek kiképzett egységek. Látogasd meg a Kaszárnyát a képzéshez.',
      },
      trainingQueue: {
        title: 'Kiképzési sor',
        loading: 'Kiképzési sor betöltése...',
        empty: 'Jelenleg nem folyik kiképzés.',
        finishesAt: 'Befejezés ideje: {time}',
        remainingLabel: 'Hátralévő idő',
        completed: 'Befejezve',
      },
    },
    expeditions: {
      title: 'Aktív expedíciók',
      manageLink: 'Kezelés',
      empty: 'Jelenleg nincs úton expedíció. Indíts rajtaütést az Expedíciók panelről.',
      distancePhase: 'Távolság {distance} mező • Fázis: {phase}',
      eta: 'Érkezés {eta}',
      statusLabel: 'Állapot',
      statusReturning: 'Hazatér',
      statusTravelling: 'Úton van',
      outboundLabel: 'Kimenet',
      returnLabel: 'Visszatérés',
      departedAt: 'Indulás: {time}',
      arrivalAt: 'Érkezés: {time}',
      returnAt: 'Hazatérés: {time}',
    },
  },
  expeditions: {
    phases: {
      outbound: 'Kimenő',
      returning: 'Hazatérő',
      completed: 'Teljesítve',
    },
    labels: {
      arrived: 'Megérkezett',
    },
  },
  sidebar: {
    brand: {
      badge: 'alfa',
      title: 'Farmer Battle',
      subtitle: 'Falufejlesztő • v0.1',
    },
    toggle: {
      expand: 'Megnyitás',
      compact: 'Összecsukás',
    },
    event: {
      title: 'Aratási fesztivál',
      countdown: '• 3 nap van hátra',
      description: 'Dupla élelemtermés a farmokon. Csatlakozz a közös küldetésekhez!',
      viewQuests: 'Küldetések megnyitása',
      eventShop: 'Esemény bolt',
    },
    resources: {
      gold: 'Arany',
      wood: 'Fa',
      clay: 'Agyag',
      iron: 'Vas',
    },
    actions: {
      build: 'Építés',
      train: 'Kiképzés',
      research: 'Kutatás',
      hotkey: '{label} (gyorsbillentyű: {key})',
    },
    nav: {
      village: {
        title: 'Falu',
        townSquare: 'Főtér',
        build: 'Építés és fejlesztések',
        storage: 'Raktár',
        market: 'Piac',
      },
      military: {
        title: 'Hadsereg',
        barracks: 'Kaszárnya',
        armory: 'Fegyverzet',
        battle: 'Csata',
        defense: 'Védelem',
      },
      world: {
        title: 'Világ',
        map: 'Világtérkép',
        expeditions: 'Expedíciók',
        tradeRoutes: 'Kereskedelmi útvonalak',
      },
      social: {
        title: 'Közösség',
        leaderboard: 'Ranglista',
        clan: 'Klán',
        mail: 'Üzenetek',
      },
    },
    profile: {
      name: 'Zsolt',
      level: 'Szint {level}',
      settings: 'Beállítások',
      logout: 'Kijelentkezés',
    },
  },
  build: {
    loading: 'Tervek összegyűjtése...',
    resources: {
      gold: { title: 'Arany', subtitle: 'Kincstár' },
      wood: { title: 'Fa', subtitle: 'Fakészlet' },
      clay: { title: 'Agyag', subtitle: 'Agyagbánya' },
      iron: { title: 'Vas', subtitle: 'Vasraktár' },
    },
    groupCount: {
      single: '{count} épület',
      multi: '{count} épület',
    },
    queue: {
      title: 'Fejlesztési sor',
      empty: 'Nincs folyamatban lévő fejlesztés. Az építőid utasításra várnak.',
      level: 'Szint {level}',
      readyNow: 'Bármelyik pillanatban kész',
      readyIn: 'Kész {duration} múlva',
    },
    notifications: {
      upgradeStarted: 'Fejlesztés elindítva!',
    },
    errors: {
      loadOverview: 'Nem sikerült betölteni az építkezési áttekintőt.',
    },
    categories: {
      economy: 'Gazdaság',
      military: 'Katonaság',
      storage: 'Raktár',
      special: 'Speciális',
      production: 'Termelés',
    },
  },
  landing: {
    hero: {
      badge: 'Üdvözlünk, Parancsnok!',
      title: {
        prefix: 'Kovácsold meg a ',
        highlight: 'faludat',
        suffix: ', képezz hatalmas seregeket, és urald a világtérképet.',
      },
      description:
        'A Farmer Battle a nyugodt falurendezést ötvözi a stratégiával. Gyűjts erőforrásokat, fejleszd az épületeidet, és vezesd győzelemre seregeidet a riválisok és kóbor barbárok ellen.',
      ctaStart: 'Indítsd el a faludat',
      ctaSignIn: 'Bejelentkezés',
    },
    features: {
      settlement: {
        title: 'Fejleszd a települést',
        description:
          'Fejleszd a termelő épületeket, tartsd egyensúlyban a készleteket, és gondoskodj a lakosokról, miközben a következő lépésen dolgozol.',
      },
      troops: {
        title: 'Képezz elit csapatokat',
        description:
          'Nyisd fel a legerősebb egységeket, hangold össze a kiképzési sorokat, és alakítsd a hadseregedet támadásra vagy védekezésre.',
      },
      world: {
        title: 'Hódítsd meg a világtérképet',
        description:
          'Terjeszd ki a befolyásod, foglalj el stratégiai mezőket, és kapaszkodj fel a ranglistán a többi parancsnok ellen.',
      },
    },
    resume: {
      title: 'Már folyik a kiképzés?',
      description:
        'Jelentkezz be, hogy folytasd az építkezéseket, kezeld seregeidet és felmérd a birodalmat.',
      cta: 'Vissza a parancsnoki székbe',
    },
  },
  auth: {
    login: {
      title: 'Üdv újra, Parancsnok',
      subtitle: 'Lépj be, hogy folytasd birodalmad építését.',
      usernameLabel: 'Felhasználónév',
      usernamePlaceholder: 'Parancsnoki neved',
      passwordLabel: 'Jelszó',
      passwordPlaceholder: '••••••••',
      submit: 'Bejelentkezés',
      submitPending: 'Bejelentkezés...',
      newHere: 'Új vagy itt?',
      registerCta: 'Hozz létre falut',
      errorInvalid: 'Ezekkel az adatokkal nem tudunk bejelentkeztetni.',
    },
    register: {
      title: 'Indítsd el az örökségedet',
      subtitle: 'Hozz létre egy fiókot, és indulásra kész falut kapsz a terjeszkedéshez.',
      usernameLabel: 'Parancsnoki név',
      usernamePlaceholder: 'Válassz egyedi nevet',
      passwordLabel: 'Jelszó',
      passwordPlaceholder: 'Legalább 6 karakter',
      confirmLabel: 'Megerősítés',
      confirmPlaceholder: 'Írd be újra a jelszót',
      submit: 'Fiók létrehozása',
      submitPending: 'Falu létrehozása...',
      haveAccount: 'Már van fiókod?',
      signInCta: 'Jelentkezz be',
      validation: {
        minLength: 'A jelszónak legalább 6 karakter hosszúnak kell lennie.',
        mismatch: 'A jelszavak nem egyeznek.',
      },
      errorGeneric: 'A regisztráció nem sikerült.',
    },
  },
};

export default messages;

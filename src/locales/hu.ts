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

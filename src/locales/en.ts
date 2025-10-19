const messages = {
  header: {
    appName: 'Farmer Battle',
    tagline: 'Build. Train. Conquer.',
    languageLabel: 'Language',
    languages: {
      en: 'English',
      hu: 'Magyar',
    },
    roleCommander: 'Commander',
    signOut: 'Sign out',
    signIn: 'Sign in',
    createAccount: 'Create account',
  },
  nav: {
    home: 'Home',
    village: 'My Village',
    leaderboard: 'Leaderboard',
    info: 'Info',
    admin: 'Admin',
  },
  sidebar: {
    brand: {
      badge: 'alpha',
      title: 'Farmer Battle',
      subtitle: 'Village Builder • v0.1',
    },
    toggle: {
      expand: 'Expand',
      compact: 'Compact',
    },
    event: {
      title: 'Harvest Festival',
      countdown: '• 3d left',
      description: 'Double food yield from farms. Join the co-op quests!',
      viewQuests: 'View Quests',
      eventShop: 'Event Shop',
    },
    resources: {
      gold: 'Gold',
      wood: 'Wood',
      clay: 'Clay',
      iron: 'Iron',
    },
    actions: {
      build: 'Build',
      train: 'Train',
      research: 'Research',
      hotkey: '{label} (hotkey {key})',
    },
    nav: {
      village: {
        title: 'Village',
        townSquare: 'Town Square',
        build: 'Build & Upgrades',
        storage: 'Storage',
        market: 'Market',
      },
      military: {
        title: 'Military',
        barracks: 'Barracks',
        armory: 'Armory',
        battle: 'Battle',
        defense: 'Defense',
      },
      world: {
        title: 'World',
        map: 'World Map',
        expeditions: 'Expeditions',
        tradeRoutes: 'Trade Routes',
      },
      social: {
        title: 'Social',
        leaderboard: 'Leaderboard',
        clan: 'Clan',
        mail: 'Mail',
      },
    },
    profile: {
      name: 'Zsolt',
      level: 'Lv. {level}',
      settings: 'Settings',
      logout: 'Logout',
    },
  },
  landing: {
    hero: {
      badge: 'Welcome Commander',
      title: {
        prefix: 'Forge your ',
        highlight: 'village',
        suffix: ', train mighty armies, and dominate the world map.',
      },
      description:
        'Farmer Battle blends chill village management with strategic warfare. Gather resources, upgrade your buildings, and lead your troops to victory against rivals and roaming barbarians.',
      ctaStart: 'Start your village',
      ctaSignIn: 'Sign in',
    },
    features: {
      settlement: {
        title: 'Evolve Your Settlement',
        description:
          'Upgrade production buildings, balance storage, and keep your citizens thriving while you plan your next move.',
      },
      troops: {
        title: 'Train Elite Troops',
        description:
          'Unlock powerful units, coordinate training queues, and customize your army composition for offense or defense.',
      },
      world: {
        title: 'Conquer the World Map',
        description:
          'Expand your influence, claim strategic tiles, and climb the global leaderboard against other commanders.',
      },
    },
    resume: {
      title: 'Already training troops?',
      description:
        'Sign in to resume construction, manage your armies, and survey the realm.',
      cta: 'Resume command',
    },
  },
  auth: {
    login: {
      title: 'Welcome back, Commander',
      subtitle: 'Log in to continue building your dominion.',
      usernameLabel: 'Username',
      usernamePlaceholder: 'Your commander name',
      passwordLabel: 'Password',
      passwordPlaceholder: '••••••••',
      submit: 'Sign in',
      submitPending: 'Signing in...',
      newHere: 'New here?',
      registerCta: 'Create a village',
      errorInvalid: 'Unable to sign in with those credentials.',
    },
    register: {
      title: 'Begin your legacy',
      subtitle: 'Create an account and receive a starter village ready for expansion.',
      usernameLabel: 'Commander name',
      usernamePlaceholder: 'Choose a unique name',
      passwordLabel: 'Password',
      passwordPlaceholder: 'At least 6 characters',
      confirmLabel: 'Confirm',
      confirmPlaceholder: 'Repeat password',
      submit: 'Create account',
      submitPending: 'Creating village...',
      haveAccount: 'Already have an account?',
      signInCta: 'Sign in',
      validation: {
        minLength: 'Password must be at least 6 characters.',
        mismatch: 'Passwords do not match.',
      },
      errorGeneric: 'Registration failed.',
    },
  },
};

export default messages;

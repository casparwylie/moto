// Initiate user state
const userState = new UserState();
userState.refresh();

// Initiate racing page
const racingPage = new RacingPage();
racingPage.checkSharedRace();

// Initiate windows
const windows = new Windows();

// Populate insights
const popularPairsInsight = new PopularPairsInsight();
popularPairsInsight.populate();

const recentRacesInsight = new RecentRacesInsight();
recentRacesInsight.populate();

// Initiate account forms
const signupForm = new SignupForm();
const loginForm = new LoginForm(userState);

var userState;
var racingPage;
var windows;
var popularPairsInsight;
var recentRacesInsight;
var signupForm;
var loginForm;
var social;

async function main() {

  // Initiate user state
  userState = new UserState();
  await userState.refresh();

  // Initiate racing page
  racingPage = new Racing();
  await racingPage.checkSharedRace();

  // Initiate windows
  windows = new Windows();

  // Populate insights
  popularPairsInsight = new PopularPairsInsight();
  await popularPairsInsight.populate();

  recentRacesInsight = new RecentRacesInsight();
  await recentRacesInsight.populate();

  // Initiate account forms
  signupForm = new SignupForm();
  loginForm = new LoginForm(userState);

  // Initiate social
  social = new Social();

  // Start intro
  intro = new Intro(racingPage);
  await intro.start();
}

main();

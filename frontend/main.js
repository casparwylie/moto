var userState;
var racingPage;
var windows;
var popularPairsInsight;
var recentRacesInsight;
var signupForm;
var loginForm;


async function main() {
  // Initiate user state
  userState = new UserState();
  await userState.refresh();

  // Initiate racing page
  racingPage = new RacingPage();
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
}

main();

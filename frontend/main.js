async function main() {
  // Initiate user state
  const userState = new UserState();
  await userState.refresh();

  // Initiate racing page
  const racingPage = new RacingPage();
  await racingPage.checkSharedRace();

  // Initiate windows
  const windows = new Windows();

  // Populate insights
  const popularPairsInsight = new PopularPairsInsight();
  await popularPairsInsight.populate();

  const recentRacesInsight = new RecentRacesInsight();
  await recentRacesInsight.populate();

  // Initiate account forms
  const signupForm = new SignupForm();
  const loginForm = new LoginForm(userState);
}

main();

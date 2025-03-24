Feature: Signup Functionality


  Scenario: Successful signup and user data stored
    Given I am on the signup page at http://localhost:3000/signup
    And I enter 'another_user' into the username field
    And I enter 'secure_password' into the password field
    When I click the 'Sign Up' button
    Then user data should be stored in local storage

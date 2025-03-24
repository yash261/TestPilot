Feature: Login Functionality


  Scenario: Successful login and user data stored
    Given I am on the login page at http://localhost:3000/
    And I enter 'user' into the username field
    And I enter 'pass' into the password field
    When I click the 'Login' button
    Then user data should be stored in local storage

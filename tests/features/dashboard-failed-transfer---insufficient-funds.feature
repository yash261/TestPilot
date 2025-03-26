Feature: Dashboard Functionality


  Scenario: Failed Transfer - Insufficient Funds
    Given I am on the login page at http://localhost:3000/
    And I enter "user" as the username and "pass" as the password
    And I click the 'Login' button
    And I am on the dashboard page at http://localhost:3000/dashboard
    When I enter a recipient in the 'to-user' field
    And I enter an amount greater than my balance in the 'amount' field
    And I click the 'Transfer' button
    Then I should see an error message indicating insufficient funds

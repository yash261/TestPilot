package com.example.banking_app.service;

import com.example.banking_app.model.Transaction;
import com.example.banking_app.model.User;
import com.example.banking_app.repository.TransactionRepository;
import com.example.banking_app.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.util.List;

@Service
public class BankingService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private TransactionRepository transactionRepository;

    @PostConstruct
    public void init() {
        // Seed initial user if none exist
        if (userRepository.count() == 0) {
            User initialUser = new User();
            initialUser.setUsername("user");
            initialUser.setPassword("pass");
            initialUser.setBalance(1000.0);
            userRepository.save(initialUser);
        }
    }

    public User login(String username, String password) {
        // Testing
        return userRepository.findByUsername(username)
                .filter(u -> u.getPassword().equals(password))
                .orElse(null);
    }

    public User signup(String username, String password) {
        if (userRepository.findByUsername(username).isPresent()) {
            return null; // Username taken
        }
        User newUser = new User();
        newUser.setUsername(username);
        newUser.setPassword(password);
        newUser.setBalance(500.0); // Initial balance
        return userRepository.save(newUser);
    }

    public boolean transfer(String fromUserId, String toUserId, double amount) {
        User fromUser = userRepository.findById(fromUserId).orElse(null);
        User toUser = userRepository.findById(toUserId).orElse(null);

        if (fromUser == null || toUser == null || fromUser.getBalance() < amount || amount <= 0) {
            return false;
        }

        fromUser.setBalance(fromUser.getBalance() - amount);
        toUser.setBalance(toUser.getBalance() + amount);
        userRepository.save(fromUser);
        userRepository.save(toUser);

        Transaction transaction = new Transaction();
        transaction.setFromUserId(fromUserId);
        transaction.setToUserId(toUserId);
        transaction.setAmount(amount);
        transactionRepository.save(transaction);

        return true;
    }

    public List<User> getUsers() {
        return userRepository.findAll();
    }

    public List<Transaction> getTransactions(String userId) {
        return transactionRepository.findByFromUserIdOrToUserId(userId, userId);
    }
}

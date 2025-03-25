package com.example.banking_app.repository;

import com.example.banking_app.model.Transaction;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;

public interface TransactionRepository extends MongoRepository<Transaction, String> {
    List<Transaction> findByFromUserIdOrToUserId(String fromUserId, String toUserId);
}

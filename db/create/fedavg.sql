CREATE TABLE IF NOT EXISTS fedavg (
    rec_time TIMESTAMP NOT NULL,
    rnd INT NOT NULL,
    learner_id INT NOT NULL,
    loss FLOAT NOT NULL,
    acc FLOAT NOT NULL,
);
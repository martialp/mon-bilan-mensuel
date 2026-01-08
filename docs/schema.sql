-- schema.sql
-- Schéma de base de données pour gestion des finances personnelles

CREATE TABLE accounts (
                          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                          name TEXT NOT NULL,
                          type TEXT NOT NULL CHECK (type IN ('credit_card', 'chequing', 'savings', 'investment', 'other')),
                          institution TEXT,
                          description TEXT,
                          created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE categories (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            name TEXT NOT NULL UNIQUE,
                            created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE categorization_rules (
                                      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                      account_id UUID REFERENCES accounts(id),  -- NULL = s'applique à tous les comptes
                                      rule TEXT NOT NULL,
                                      created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE transactions (
                              id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                              account_id UUID NOT NULL REFERENCES accounts(id),
                              date_transaction DATE NOT NULL,
                              date_inscription DATE,
                              description TEXT NOT NULL,
                              amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                              type TEXT NOT NULL CHECK (type IN ('expense', 'income', 'transfer')),
                              category_id UUID REFERENCES categories(id),
                              status TEXT DEFAULT 'auto' CHECK (status IN ('auto', 'confirmed', 'manual')),
                              note TEXT,
                              source_file TEXT,
                              statement_date DATE,
                              created_at TIMESTAMPTZ DEFAULT NOW(),

                              UNIQUE(account_id, date_transaction, description, amount_cents, statement_date)
);
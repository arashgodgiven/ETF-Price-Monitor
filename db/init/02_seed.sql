-- ============================================================
-- ETF Monitor — Seed Script
-- Loads prices.csv into the prices hypertable (idempotent).
-- ============================================================

DO $$
BEGIN
	IF (SELECT COUNT(*) FROM prices) = 0 THEN
		RAISE NOTICE 'Seeding prices table from CSV...';

		-- CSV is wide format (DATE, A, B, ..., Z). Stage then unpivot.
		CREATE TEMP TABLE prices_wide (
			date DATE,
			"A" NUMERIC(12,4), "B" NUMERIC(12,4), "C" NUMERIC(12,4),
            "D" NUMERIC(12,4), "E" NUMERIC(12,4), "F" NUMERIC(12,4),
            "G" NUMERIC(12,4), "H" NUMERIC(12,4), "I" NUMERIC(12,4),
            "J" NUMERIC(12,4), "K" NUMERIC(12,4), "L" NUMERIC(12,4),
            "M" NUMERIC(12,4), "N" NUMERIC(12,4), "O" NUMERIC(12,4),
            "P" NUMERIC(12,4), "Q" NUMERIC(12,4), "R" NUMERIC(12,4),
            "S" NUMERIC(12,4), "T" NUMERIC(12,4), "U" NUMERIC(12,4),
            "V" NUMERIC(12,4), "W" NUMERIC(12,4), "X" NUMERIC(12,4),
            "Y" NUMERIC(12,4), "Z" NUMERIC(12,4)
		);

		COPY prices_wide FROM '/seed/prices.csv' WITH (FORMAT csv, HEADER true);

		INSERT INTO prices (date, stock_name, close_price)
		SELECT
			p.date,
			s.stock_name,
			s.price
		FROM prices_wide p
		CROSS JOIN LATERAL (
			VALUES
				('A', p."A"), ('B', p."B"), ('C', p."C"), ('D', p."D"),
                ('E', p."E"), ('F', p."F"), ('G', p."G"), ('H', p."H"),
                ('I', p."I"), ('J', p."J"), ('K', p."K"), ('L', p."L"),
                ('M', p."M"), ('N', p."N"), ('O', p."O"), ('P', p."P"),
                ('Q', p."Q"), ('R', p."R"), ('S', p."S"), ('T', p."T"),
                ('U', p."U"), ('V', p."V"), ('W', p."W"), ('X', p."X"),
                ('Y', p."Y"), ('Z', p."Z")
		) AS s(stock_name, price)
		ON CONFLICT (date, stock_name) DO NOTHING;

		DROP TABLE prices_wide;

		RAISE NOTICE 'Prices seeded successfully.';
	ELSE
		RAISE NOTICE 'Skipping seed. Prices table already populated.';
	END IF;
END $$;
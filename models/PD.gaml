/**
* Name: PD
* Based on the internal skeleton template.
* Author: szydzi7681
* Tags:
*/

model PD

global {
	/** Insert the global definitions, variables and actions here */
	file park_boundary_shapefile <- file("../includes/gis/drogi.geojson");
	file park_paths_shapefile <- file("../includes/gis/drogi.geojson");
	graph path_network;

	bool real_env <- true;
	bool unlimited_games <- false;

	bool show_social_links <- true;
	float social_link_threshold <- 0.3;

	int nb_game <- 0;
	map<string, game> active_pairs <- [];

	list<string> characters <- ["TFT","QLEARN","AQLEARN","ALLC","ALLD","FTFT","TF2T","GRIM","WSLS"];
	list<string> character_pool;

	int nb_QLEARN <- 0;
	int nb_AQLEARN <- 0;
	int nb_TFT <- 0;
	int nb_ALLC <- 0;
	int nb_ALLD <- 0;
	int nb_FTFT <- 0;
	int nb_TF2T <- 0;
	int nb_GRIM <- 0;
	int nb_WSLS <- 0;

	float env_influence_qlearn <- 0.0;
	float social_sensitivity_aqlearn <- 0.0;
	float social_learning_boost_aqlearn <- 0.0;
	float movement_sensitivity <- 2.0;
	float broken_windows_sensitivity <- 0.0;
	float disorder_bump_dd <- 0.15;   // obopólna, jawna defekcja - mocniejszy sygnał
	float disorder_bump_d <- 0.08;    // pojedyncza defekcja
	float disorder_decay <- 0.98;
	bool disorder_clamp <- false;     // true: disorder ograniczony do [0, 1] (bez tego rośnie bez limitu)
	int generalization_threshold <- 3;

	string base_character_qlearn <- "TFT";
	float character_strength_qlearn <- 0.0;
	float anchor_decay_rate <- 0.15;  // wykładniczy zanik kotwicy - ustaliliśmy, że lepiej pasuje do "punktu krytycznego" niż harmoniczny

	float disorder_bump_for(string m1, string m2) {
	    if m1 = "D" and m2 = "D" { return disorder_bump_dd; }
	    if m1 = "D" or m2 = "D" { return disorder_bump_d; }
	    return 0.0;
	}

	float recent_defection_rate(int window) {
	    list<string> recent_moves <- [];
	    loop p over: player {
	        loop lst over: p.my_moves_per_other.values {
	            recent_moves <- recent_moves + last(min(window, length(lst)), lst);
	        }
	    }
	    if empty(recent_moves) { return 0.0; }
	    int d_count <- length(recent_moves where (each = "D"));
	    return d_count / length(recent_moves);
	}

	int end_cycle <- 50000;
	string variant_name <- "unset";
	bool log_games <- true;  // zapis każdej gry do konsoli i PD.csv - wyłączane w batchach

	// --- diagnostyka: odcisk przebiegu (test regresyjny nr 1) i pomiar wydajności ---
	// nic tu nie losuje i nie wpływa na dynamikę
	int nb_moves_C <- 0;
	int nb_moves_D <- 0;
	int nb_exploitations <- 0;        // gry C-D: jedna strona wyzyskana (miara zysku oszustów, P3)
	bool regression_export <- false;
	int regression_cycle <- 2000;
	bool perf_log <- false;
	int perf_interval <- 100;
	float perf_last_time <- 0.0;

	int vision_radius <- 10;
	int world_size <- 10;

	geometry shape <- real_env ? envelope(park_boundary_shapefile) : square(world_size);

	// wypłaty jako float (słaby PD / snowdrift); wartości domyślne = wersja JASSS
	float payoff_R <- 5.0;
	float payoff_P <- 1.0;
	float payoff_T <- 9.0;
	float payoff_S <- 0.0;
	string game_type <- "PD";   // "PD": T>R>P>S, "weak_PD": T>R>P=S, "snowdrift": T>R>S>P

	// TFT/TF2T/WSLS przy pierwszym spotkaniu: false = losowo 50/50 (JASSS), true = C (klasycznie)
	bool classic_start_cooperate <- false;

	// --- Moduł 1: limit Dunbara ---
	int dunbar_limit <- 0;        // 0 = brak limitu (moduł wyłączony)
	int partner_window <- 500;    // okno (cykle) dla metryki "różni partnerzy na agenta"
	int nb_forgets_total <- 0;
	int nb_forgets_prev <- 0;
	int forgets_last_cycle <- 0;  // zapomnienia w poprzednim cyklu (reflex świata biegnie przed graczami)

	// udział gier C-D wśród wszystkich gier - do P3 (zysk oszustów przy zapominaniu)
	float exploitation_rate() {
		return nb_game = 0 ? 0.0 : nb_exploitations / nb_game;
	}

	float mean_known_partners() {
		return empty(player) ? 0.0 : mean(player collect length(each.known_others));
	}

	float mean_distinct_partners_window() {
		return empty(player) ? 0.0 : mean(player collect each.distinct_partners_in_window());
	}

	// udział agentów, którzy w oknie spotkali więcej różnych partnerów niż dunbar_limit;
	// bliski 0 => limit w tej konfiguracji praktycznie nie działa
	float share_exceeding_dunbar() {
		if empty(player) or dunbar_limit <= 0 { return 0.0; }
		return length(player where (each.distinct_partners_in_window() > dunbar_limit)) / length(player);
	}

	reflex track_forgets {
		forgets_last_cycle <- nb_forgets_total - nb_forgets_prev;
		nb_forgets_prev <- nb_forgets_total;
	}

	// --- Moduł 2: ewolucyjna zmiana strategii (imitacja Fermiego + mutacja) ---
	bool evolution_on <- false;
	int evolution_interval <- 100;   // co ile cykli
	float fermi_k <- 0.5;            // szum selekcji K
	float mutation_rate <- 0.0;
	list<string> evolvable_characters <- ["TFT", "ALLC", "ALLD", "FTFT", "TF2T", "GRIM", "WSLS"];
	bool well_mixed <- false;        // kontrola: pary i modele losowane z całej populacji, bez przestrzeni
	int nb_character_changes <- 0;

	// szeregi czasowe udziałów charakterów (osobny CSV, wiersz = próbkowany cykl)
	bool timeseries_export <- false;
	int sample_interval <- 100;
	int ts_prev_C <- 0;
	int ts_prev_D <- 0;

	float fermi_probability(float pi_model, float pi_self) {
		float x <- -(pi_model - pi_self) / fermi_k;
		if x > 50 { return 0.0; }
		if x < -50 { return 1.0; }
		return 1 / (1 + exp(x));
	}

	float share_of(string ch) {
		return empty(player) ? 0.0 : length(player where (each.character = ch)) / length(player);
	}

	// aktualizacja synchroniczna: najpierw wszystkie decyzje na starych charakterach i π, potem zmiana;
	// okno wypłat zerowane u wszystkich po aktualizacji
	reflex evolve when: evolution_on and cycle > 0 and every(evolution_interval) {
		do evolution_step();
	}

	action evolution_step() {
		map<player, string> decisions <- map<player, string>([]);
		loop p over: player where (each.character in evolvable_characters) {
			decisions[p] <- p.evolution_choice(p.pick_model());
		}
		loop p over: decisions.keys {
			string new_char <- decisions[p];
			ask p { do change_character(new_char); }
		}
		ask player {
			window_payoff <- 0.0;
			window_games <- 0;
		}
	}

	// --- Etap 1: eksperyment kompatybilności ---
	bool compat_core <- false;        // rdzeń: tylko strategie klasyczne; bez disorder, kotwicy, Q-learningu, ruchu środowiskowego/społecznego
	int compat_N <- 200;              // liczebność populacji w rdzeniu
	string compat_mix <- "equal";     // "equal": po równo 7 klasycznych; "tft_alld": 80% TFT + 20% ALLD (P3)
	string payoff_preset <- "custom"; // "PD_classic", "weak_PD", "snowdrift"; "custom" = wartości z parametrów
	string prediction <- "";          // etykieta wiersza w compat_results.csv
	bool compat_export <- false;
	int warmup <- 5000;               // cykle wygrzewania przed oceną stabilizacji
	int stab_window <- 1000;          // okno średniej kroczącej udziałów
	float stab_eps <- 0.01;           // maks. zmiana średnich między kolejnymi oknami
	int stab_k <- 5;                  // tyle kolejnych okien ze zmianą < eps = stabilizacja
	list<string> classic_characters <- ["TFT", "ALLC", "ALLD", "FTFT", "TF2T", "GRIM", "WSLS"];
	// stan wykrywania stabilizacji (wektor = udziały 7 klasycznych + udział D w próbce)
	list<float> stab_sum <- [];
	int stab_samples <- 0;
	list<float> stab_prev <- [];
	list<float> stab_last <- [];
	int stab_count <- 0;
	int stabilized_at <- -1;
	int stab_prev_C <- 0;
	int stab_prev_D <- 0;
	int win_games0 <- 0;
	int win_expl0 <- 0;
	float exploit_last_window <- 0.0;

	action apply_payoff_preset() {
		if payoff_preset = "PD_classic" {
			game_type <- "PD"; payoff_T <- 9.0; payoff_R <- 5.0; payoff_P <- 1.0; payoff_S <- 0.0;
		} else if payoff_preset = "weak_PD" {
			game_type <- "weak_PD"; payoff_T <- 1.6; payoff_R <- 1.0; payoff_P <- 0.0; payoff_S <- 0.0;
		} else if payoff_preset = "snowdrift" {
			game_type <- "snowdrift"; payoff_T <- 4.0; payoff_R <- 3.0; payoff_S <- 2.0; payoff_P <- 0.0;
		}
	}

	// wyłącza wszystko spoza rdzenia i ustala skład populacji
	action apply_compat_core() {
		nb_QLEARN <- 0;
		nb_AQLEARN <- 0;
		movement_sensitivity <- 0.0;          // losowy ruch po sieci
		env_influence_qlearn <- 0.0;
		social_sensitivity_aqlearn <- 0.0;
		social_learning_boost_aqlearn <- 0.0;
		broken_windows_sensitivity <- 0.0;
		character_strength_qlearn <- 0.0;
		unlimited_games <- true;
		classic_start_cooperate <- true;
		if compat_mix = "tft_alld" {
			nb_ALLD <- round(compat_N * 0.2);
			nb_TFT <- compat_N - nb_ALLD;
			nb_ALLC <- 0; nb_FTFT <- 0; nb_TF2T <- 0; nb_GRIM <- 0; nb_WSLS <- 0;
		} else {
			int base <- compat_N div 7;
			int rest <- compat_N mod 7;
			nb_TFT <- base + (rest > 0 ? 1 : 0);
			nb_ALLC <- base + (rest > 1 ? 1 : 0);
			nb_ALLD <- base + (rest > 2 ? 1 : 0);
			nb_FTFT <- base + (rest > 3 ? 1 : 0);
			nb_TF2T <- base + (rest > 4 ? 1 : 0);
			nb_GRIM <- base + (rest > 5 ? 1 : 0);
			nb_WSLS <- base;
		}
	}

	// nazwy mechanizmów spoza rdzenia, które są aktywne (pusta lista = czysty rdzeń)
	list<string> core_violations() {
		list<string> v <- [];
		if nb_QLEARN > 0 or nb_AQLEARN > 0 or !empty(player where (each.character in ["QLEARN", "AQLEARN"])) { v <+ "Q-learning"; }
		if movement_sensitivity != 0 or !empty(player where (each.sensitivity != 0)) { v <+ "ruch środowiskowy"; }
		if social_sensitivity_aqlearn != 0 or !empty(player where (each.social_sensitivity != 0)) { v <+ "ruch społeczny"; }
		if env_influence_qlearn != 0 or social_learning_boost_aqlearn != 0 { v <+ "uczenie środowiskowe/społeczne"; }
		if broken_windows_sensitivity != 0 { v <+ "rozbita szyba"; }
		if character_strength_qlearn != 0 or !empty(player where (each.character_strength != 0)) { v <+ "kotwica"; }
		if !unlimited_games { v <+ "limit gier"; }
		return v;
	}

	// średnia krocząca udziałów w oknach stab_window; stabilizacja = stab_k kolejnych okien ze zmianą < stab_eps
	reflex track_stability when: compat_export and cycle > 0 and every(sample_interval) {
		list<float> v <- classic_characters collect (world.share_of(each));
		int d_c <- nb_moves_C - stab_prev_C;
		int d_d <- nb_moves_D - stab_prev_D;
		stab_prev_C <- nb_moves_C;
		stab_prev_D <- nb_moves_D;
		v <+ ((d_c + d_d) = 0 ? 0.0 : d_d / (d_c + d_d));
		if cycle > warmup {
			if empty(stab_sum) { stab_sum <- list_with(length(v), 0.0); }
			loop i from: 0 to: length(v) - 1 { stab_sum[i] <- stab_sum[i] + v[i]; }
			stab_samples <- stab_samples + 1;
			if stab_samples * sample_interval >= stab_window {
				list<float> mean_v <- stab_sum collect (each / stab_samples);
				if !empty(stab_prev) {
					float change <- 0.0;
					loop i from: 0 to: length(mean_v) - 1 { change <- max(change, abs(mean_v[i] - stab_prev[i])); }
					stab_count <- change < stab_eps ? stab_count + 1 : 0;
					if stab_count >= stab_k and stabilized_at < 0 { stabilized_at <- cycle; }
				}
				stab_prev <- mean_v;
				stab_last <- mean_v;
				stab_sum <- [];
				stab_samples <- 0;
				exploit_last_window <- (nb_game - win_games0) = 0 ? 0.0 : (nb_exploitations - win_expl0) / (nb_game - win_games0);
				win_games0 <- nb_game;
				win_expl0 <- nb_exploitations;
			}
		}
	}

	// wiersz = przebieg; udziały i udział D to średnie z ostatniego pełnego okna
	reflex export_compat when: compat_export and cycle = end_cycle {
		list<float> fin <- empty(stab_last) ? ((classic_characters collect (world.share_of(each))) + [0.0]) : stab_last;
		float share_TFT <- fin[0];
		float share_ALLC <- fin[1];
		float share_ALLD <- fin[2];
		float share_FTFT <- fin[3];
		float share_TF2T <- fin[4];
		float share_GRIM <- fin[5];
		float share_WSLS <- fin[6];
		float d_share <- fin[7];
		float payoff_ALLD <- mean_for("ALLD") / 1000;
		float payoff_TFT <- mean_for("TFT") / 1000;
		float payoff_all <- mean_score_all() / 1000;
		float known_partners <- mean_known_partners();
		float distinct_partners <- mean_distinct_partners_window();
		float exceeding_dunbar <- share_exceeding_dunbar();
		bool fixated <- !empty(classic_characters where (world.share_of(each) >= 1.0));
		bool stabilized <- stab_count >= stab_k;
		save [variant_name, prediction, seed, compat_N, well_mixed, payoff_preset, payoff_T, payoff_R, payoff_P, payoff_S,
			evolution_on, mutation_rate, fermi_k, evolution_interval, dunbar_limit, vision_radius, end_cycle,
			share_TFT, share_ALLC, share_ALLD, share_FTFT, share_TF2T, share_GRIM, share_WSLS, d_share,
			exploit_last_window, payoff_ALLD, payoff_TFT, payoff_all, known_partners, distinct_partners,
			exceeding_dunbar, fixated, stabilized, stabilized_at, nb_character_changes]
			to: "../results/compat_results.csv" rewrite: false format: "csv" header: true;
	}

	reflex export_timeseries when: timeseries_export and every(sample_interval) {
		int d_c <- nb_moves_C - ts_prev_C;
		int d_d <- nb_moves_D - ts_prev_D;
		ts_prev_C <- nb_moves_C;
		ts_prev_D <- nb_moves_D;
		float d_share <- (d_c + d_d) = 0 ? 0.0 : d_d / (d_c + d_d);
		save [variant_name, seed, cycle, share_of("TFT"), share_of("ALLC"), share_of("ALLD"), share_of("FTFT"),
			share_of("TF2T"), share_of("GRIM"), share_of("WSLS"), share_of("QLEARN"), share_of("AQLEARN"),
			d_share, nb_character_changes]
			to: "../results/character_timeseries.csv" rewrite: false format: "csv" header: true;
	}

	bool payoffs_valid() {
		if game_type = "PD" { return payoff_T > payoff_R and payoff_R > payoff_P and payoff_P > payoff_S; }
		if game_type = "weak_PD" { return payoff_T > payoff_R and payoff_R > payoff_P and payoff_P = payoff_S; }
		if game_type = "snowdrift" { return payoff_T > payoff_R and payoff_R > payoff_S and payoff_S > payoff_P; }
		return false;
	}

	bool payoffs_integer() {
		return payoff_T = round(payoff_T) and payoff_R = round(payoff_R)
			and payoff_P = round(payoff_P) and payoff_S = round(payoff_S);
	}

	int grid_cols <- 50;
	int grid_rows <- 50;
	float cell_learning_rate <- 0.1;

	int selected_index <- 0;

	player selected_player() {
		list<player> all_players <- list(player);
		if empty(all_players) {
			return nil;
		}
		int idx <- min(selected_index, length(all_players) - 1);
		return all_players[idx];
	}

	float feedback_value(string my_move, string opp_move) {
		if my_move = "C" and opp_move = "C" {
			return 0.1;
		}
		if my_move = "D" and opp_move = "D" {
			return -0.8;
		}
		if my_move = "D" and opp_move = "C" {
			return 1.0;
		}
		if my_move = "C" and opp_move = "D" {
			return -1.0;
		}
		return 0.0;
	}

	float average_feedback(environment_cell cell) {
		list<float> values <- [];
		loop p over: player {
			if cell in p.personal_feedback.keys {
				values <+ p.personal_feedback[cell];
			}
		}
		return empty(values) ? 0.0 : mean(values);
	}

	float normalized_visual_height(player p) {
		list<float> values <- player collect each.for_chart;

		if empty(values) {
			return 0.0;
		}

		float v_min <- min(values);
		float v_max <- max(values);

		if v_max = v_min {
			return 0.0;
		}

		return 10 * (p.for_chart - v_min) / (v_max - v_min);
	}

	float mean_for(string ch) {
		list<player> group <- player where (each.character = ch and each.nb_games > 0);
		if empty(group) {
			return 0.0;
		}
		return mean(group collect (each.score / each.nb_games * 1000));
	}

	float mean_score_all() {
		list<player> group <- player where (each.nb_games > 0);
		if empty(group) {
			return 0.0;
		}
		return mean(group collect (each.score / each.nb_games * 1000));
	}

	float mean_for_classic() {
		list<string> classic <- ["TFT", "ALLC", "ALLD", "FTFT", "TF2T", "GRIM", "WSLS"];
		list<player> group <- player where (each.nb_games > 0 and (each.character in classic));
		if empty(group) {
			return 0.0;
		}
		return mean(group collect (each.score / each.nb_games * 1000));
	}

	float aqlearn_clique_fraction() {
		list<player> aq <- player where (each.character = "AQLEARN");
		int total <- 0;
		int high <- 0;
		loop p over: aq {
			loop q over: aq {
				if p!= q {
					total <- total + 1;
					float v <- (q in p.social_feedback.keys) ? p.social_feedback[q] : 0.0;
					if v > 0.5 {
						high <- high + 1;
					}
				}
			}
		}
		return total = 0 ? 0.0 : (high / total);
	}

	float aqlearn_avg_distance() {
		list<player> aq <- player where (each.character = "AQLEARN");
		if length(aq) < 2 {
			return 0.0;
		}
		list<float> dists <- [];
		loop i from: 0 to: length(aq) - 1 {
			loop j from: i + 1 to: length(aq) - 1 {
				dists <+ (aq[i].location distance_to aq[j].location);
			}
		}
		return mean(dists);
	}

	reflex export_metrics when: cycle = end_cycle {
		save [
			variant_name,
			mean_score_all(),
			mean_for("QLEARN"),
			mean_for("AQLEARN"),
			mean_for_classic(),
			aqlearn_clique_fraction(),
			aqlearn_avg_distance()
		] to: "../results/ablation_results.csv" rewrite: false format: "csv" header: true;
	}

	// odcisk przebiegu: przy tym samym seedzie i wyłączonych modułach musi być identyczny przed i po zmianach
	reflex export_regression_fingerprint when: regression_export and cycle = regression_cycle {
		float score_sum <- 0.0;
		float score_weighted <- 0.0;   // ważona pozycją - wykrywa też zamianę wyników między agentami
		float loc_sum <- 0.0;          // wykrywa rozjazd trajektorii
		float q_sum <- 0.0;
		int i <- 1;
		loop p over: player sort_by each.name {
			score_sum <- score_sum + float(p.score);
			score_weighted <- score_weighted + i * float(p.score);
			loc_sum <- loc_sum + i * (p.location.x + p.location.y);
			loop m over: p.q_c_per_other.values { q_sum <- q_sum + sum(m.values); }
			loop m over: p.q_d_per_other.values { q_sum <- q_sum - sum(m.values); }
			i <- i + 1;
		}
		float disorder_sum <- sum(environment_cell collect each.disorder);
		save [variant_name, unlimited_games, seed, cycle, nb_game, nb_moves_C, nb_moves_D,
			score_sum, score_weighted, loc_sum, q_sum, disorder_sum]
			to: "../results/regression_fingerprint.csv" rewrite: false format: "csv" header: true;
	}

	// czas cyklu w ms, uśredniony po perf_interval cyklach
	reflex perf_measure when: perf_log and every(perf_interval) {
		float now <- machine_time;
		if cycle > 0 {
			float ms_per_cycle <- (now - perf_last_time) / perf_interval;
			write "[perf] cykl " + cycle + " N=" + length(player) + ": " + ms_per_cycle + " ms/cykl";
			save [variant_name, length(player), cycle, ms_per_cycle]
				to: "../results/perf.csv" rewrite: false format: "csv" header: true;
		}
		perf_last_time <- now;
	}

	string pair_key(player a, player b) {
		return (a.name < b.name) ? (a.name + "|" + b.name) : (b.name + "|" + a.name);
	}

	init {
		do apply_payoff_preset();
		if compat_core { do apply_compat_core(); }
		if not payoffs_valid() {
			error "Macierz wypłat niezgodna z game_type=" + game_type
				+ " (PD: T>R>P>S, weak_PD: T>R>P=S, snowdrift: T>R>S>P).
Aktualnie : T=" + payoff_T + " R=" + payoff_R + " P=" + payoff_P + " S=" + payoff_S;
		}
		// height jest licznikiem cykli blokady - przy ograniczeniu gier wypłaty muszą być całkowite
		if not unlimited_games and not payoffs_integer() {
			error "Tryb z ograniczeniem gier (unlimited_games=false) wymaga całkowitych wypłat.";
		}
		if game_type = "PD" and not (2 * payoff_R > payoff_T + payoff_S) {
			write "OSTRZEŻENIE: 2R <= T+S (" + (2*payoff_R) + " <= " + (payoff_T + payoff_S) + ")
- naprzemienna eksploatacja nie jest gorsza niż stała kooperacja.";
		}

		create park_boundary from: park_boundary_shapefile;
		create path_segment from: park_paths_shapefile;
		path_network <- as_edge_graph(path_segment);

		map<string,int> counts <- [
			"QLEARN"::nb_QLEARN,
			"AQLEARN"::nb_AQLEARN,
			"TFT"::nb_TFT,
			"ALLC"::nb_ALLC,
			"ALLD"::nb_ALLD,
			"FTFT"::nb_FTFT,
			"TF2T"::nb_TF2T,
			"GRIM"::nb_GRIM,
			"WSLS"::nb_WSLS
		];

		loop k over: counts.keys {
			loop times: counts[k] {
				character_pool <+ k;
			}
		}
		if not empty(character_pool){
			loop i from: 0 to: length(character_pool) - 1 {
				create player {
					character <- character_pool[i];
					do apply_character_params();
					// mapy per przeciwnik zakładane leniwie przy pierwszej grze (ensure_partner) -
					// zamiast O(N^2) setup_lists; bez losowania, więc wyniki bez zmian
					if real_env {
						do init_on_network();
					}
				}
			}
		}
	}
}

species park_boundary {
	aspect default {
		draw shape color: #forestgreen border: #darkgreen ;
	}
}

grid environment_cell width: grid_cols height: grid_rows neighbors: 8 {

	float disorder <- 0.0;

	reflex decay_disorder when: every(10) {
	    do apply_decay();
	}

	action apply_decay() {
		disorder <- disorder * disorder_decay;
	}

	rgb summary_color() {
		float fb <- world.average_feedback(self);
		if fb > 0 {
			return rgb(255 * (1 - fb), 255, 255 * (1 - fb));
		} else if fb < 0 {
			return rgb(255, 255 * (1 + fb), 255 * (1 + fb));
		}
		return #white;
	}

	rgb personal_color(player p) {
		if p = nil {
			return #white;
		}
		float fb <- (self in p.personal_feedback.keys) ? p.personal_feedback[self] : 0.0;
		if fb > 0 {
			return rgb(255 * (1 - fb), 255, 255 * (1 - fb));
		} else if fb < 0 {
			return rgb(255, 255 * (1 + fb), 255 * (1 + fb));
		}
		return #white;
	}
	aspect summary {
		draw shape color: summary_color();
	}
	aspect personal {
		draw shape color: personal_color(world.selected_player());
	}
	aspect default {
		draw shape color: #white border: #lightgrey;
	}
}

species path_segment {
	aspect default {
		draw shape color: #sienna width: 2;
	}
}

species game{
	string pair_key;
	player p1;
	player p2;
	string p1_move;
	string p2_move;
	int lifespan <- 10;


	init {
		nb_game <- nb_game + 1;
		player first_player <- p1;
		player second_player <- p2;
		ask p1 { do ensure_partner(second_player); }
		ask p2 { do ensure_partner(first_player); }
		p1_move <- p1.strategy(p2);
		p2_move <- p2.strategy(p1);
		// THS IS SETTELED p1.move;
		player opponent_of_p1 <- p2;
		player opponent_of_p2 <- p1;

		float fb_p1 <- world.feedback_value(p1_move, p2_move);
		float fb_p2 <- world.feedback_value(p2_move, p1_move);

		environment_cell cell_p1 <- environment_cell(p1.location);
		environment_cell cell_p2 <- environment_cell(p2.location);

		ask p1 {
			do update_personal_feedback(cell_p1, fb_p1);
			do update_social_feedback(opponent_of_p1, fb_p1);
			if myself.p2_move = "D" { do register_betrayal(cell_p1); }
		}

		ask p2 {
			do update_personal_feedback(cell_p2, fb_p2);
			do update_social_feedback(opponent_of_p2, fb_p2);
			if myself.p1_move = "D" { do register_betrayal(cell_p2); }
		}

		float p1_payoff <- 0.0;
		float p2_payoff <- 0.0;


		if p1_move = "D" and p2_move = "D" {
			p2_payoff <- payoff_P;
			p1_payoff <- payoff_P;

		} else if p1_move = "C" and p2_move = "C" {
			p2_payoff <- payoff_R;
			p1_payoff <- payoff_R;

		} else if p1_move = "D" and p2_move = "C" {
			p2_payoff <- payoff_S;
			p1_payoff <- payoff_T;

		} else if p1_move = "C" and p2_move = "D" {
			p2_payoff <- payoff_T;
			p1_payoff <- payoff_S;
		}

		// liczniki ruchów - odcisk regresyjny i udział defekcji
		nb_moves_D <- nb_moves_D + (p1_move = "D" ? 1 : 0) + (p2_move = "D" ? 1 : 0);
		if (p1_move = "D" and p2_move = "C") or (p1_move = "C" and p2_move = "D") {
			nb_exploitations <- nb_exploitations + 1;
		}
		nb_moves_C <- nb_moves_C + (p1_move = "C" ? 1 : 0) + (p2_move = "C" ? 1 : 0);

		float bump <- world.disorder_bump_for(p1_move, p2_move);
		if bump > 0 {
		    ask cell_p1 { disorder <- disorder_clamp ? min(1.0, disorder + bump) : disorder + bump; }
		    if cell_p2 != cell_p1 {
		        ask cell_p2 { disorder <- disorder_clamp ? min(1.0, disorder + bump) : disorder + bump; }
		    }
		}

		if unlimited_games {
			p2.score <- p2.score + p2_payoff;
			p1.score <- p1.score + p1_payoff;
		} else {
			p2.height <- p2.height + int(p2_payoff);
			p1.height <- p1.height + int(p1_payoff);
		}

		p2.lists_per_other[p1] <+ p1_move;
		p2.my_moves_per_other[p1] <+ p2_move;

		p1.lists_per_other[p2] <+ p2_move;
		p1.my_moves_per_other[p2] <+ p1_move;

		p1.nb_games <- p1.nb_games + 1;
		p2.nb_games <- p2.nb_games + 1;

		// Moduł 2: π = średnia wypłata na grę w bieżącym oknie ewolucji
		p1.window_payoff <- p1.window_payoff + p1_payoff;
		p1.window_games <- p1.window_games + 1;
		p2.window_payoff <- p2.window_payoff + p2_payoff;
		p2.window_games <- p2.window_games + 1;

		if p1.character = "QLEARN" or p1.character = "AQLEARN"{
			float payoff_of_p1 <- p1_payoff;
			ask p1 {
				do update_q(opponent_of_p1, payoff_of_p1);
			}
		}

		if p2.character = "QLEARN" or p2.character = "AQLEARN"{
			float payoff_of_p2 <- p2_payoff;
			ask p2 {
				do update_q(opponent_of_p2, payoff_of_p2);
			}
		}

//		write "cycle[" + cycle + "] Gra między " + p2 + " i " + p1 + ".
//		p2 move: " + p2_move + ". p1 move: " + p1_move + ".
//		p2 score: " + p2.score + ". p1 score: " + p1.score + ".";

		ask p1 { do touch_partner(second_player); }
		ask p2 { do touch_partner(first_player); }

		if log_games {
			write "" + nb_game + "," + cycle + "," + p1 + "," + p2 + "," + p1_move + "," + p2_move + "," + p1.score + "," + p2.score;
			save [nb_game,cycle,p1,p2,p1_move,p2_move,p1.score,p2.score]
				rewrite: false to: "../results/PD.csv" format: "csv" header: true;
		}
    }


	reflex die{
		lifespan <- lifespan - 1;
		if lifespan = 0{
			remove key: pair_key from: world.active_pairs;
			do die();
		}
	}

	aspect default{
		draw circle(5) color: #red;
	}
}

species player skills: [moving] {

	int height <- 0;
	float score <- 0.0;
	float for_chart -> nb_games > 0 ? (score / nb_games * 1000) : 0.0;
	list<player> known_others;               // LRU: najdawniej widziany na początku
	map<player, int> last_met_cycle;         // tylko metryka okna - nie jest pamięcią strategii
	int nb_forgotten <- 0;
	float window_payoff <- 0.0;              // Moduł 2: suma wypłat w bieżącym oknie
	int window_games <- 0;
	map<player, int> history_offset;         // Moduł 2: GRIM liczy historię od tego miejsca (przejęcie charakteru)
	string character;
	player enemy;
	float forgiveness  <- 0.05;
	int nb_games;

	point current_node;
	point target_node;
	float move_speed <- 2.0;
	float sensitivity <- 2.0;

	map<player, float> social_feedback;
	float social_learning_rate <- 0.1;
	float social_sensitivity <- 0.0;
	float social_learning_boost <- 0.0;
	float env_influence <- 0.0;
	float initial_cooperation_bias <- min(1.0, max(0.0, gauss(0.5, 0.15)));

	string base_character <- "TFT";
	float character_strength <- 0.0;
	map<environment_cell, int> betrayal_count_at_location;

	// parametry zależne od charakteru - wydzielone z global.init, żeby dało się je testować
	action apply_character_params() {
		sensitivity <- movement_sensitivity;
		if character = "AQLEARN" {
			social_sensitivity <- social_sensitivity_aqlearn;
			social_learning_boost <- social_learning_boost_aqlearn;
		}
		if character = "QLEARN" or character = "AQLEARN" {
			env_influence <- env_influence_qlearn;
			base_character <- base_character_qlearn;
			character_strength <- character_strength_qlearn;
		}
	}

	// Moduł 2: model do imitacji - losowy sąsiad w zasięgu widzenia (well_mixed: losowy agent populacji)
	player pick_model() {
		list<player> pool <- well_mixed ? (list(player) - self) : ((player at_distance(vision_radius)) - [self]);
		return empty(pool) ? nil : one_of(pool);
	}

	// nowy charakter po kroku ewolucji (albo obecny); bez skutków ubocznych poza losowaniem
	string evolution_choice(player model) {
		if flip(mutation_rate) { return one_of(evolvable_characters); }
		if model = nil or model = self or not (model.character in evolvable_characters) { return character; }
		// π nieokreślone, gdy ktoś nie grał w oknie - brak imitacji
		if window_games = 0 or model.window_games = 0 { return character; }
		float pi_self <- window_payoff / window_games;
		float pi_model <- model.window_payoff / model.window_games;
		return flip(world.fermi_probability(pi_model, pi_self)) ? model.character : character;
	}

	// zmiana charakteru: pamięć partnerów zostaje, GRIM zaczyna liczyć zdrady od teraz
	action change_character(string new_char) {
		if new_char = character { return; }
		character <- new_char;
		do apply_character_params();
		loop o over: lists_per_other.keys {
			history_offset[o] <- length(lists_per_other[o]);
		}
		nb_character_changes <- nb_character_changes + 1;
	}

	action register_betrayal(environment_cell cell) {
	    if cell = nil { return; }
	    int old_val <- (cell in betrayal_count_at_location.keys) ? betrayal_count_at_location[cell] : 0;
	    betrayal_count_at_location[cell] <- old_val + 1;
	}

	string get_state(player p) {
	    string base_state;
	    if lists_per_other[p] = [] {
	        base_state <- "START";
	    } else {
	        base_state <- last(my_moves_per_other[p]) + "|" + last(lists_per_other[p]);
	    }
	    environment_cell here <- environment_cell(location);
	    bool risky <- (here != nil)
	        and (here in betrayal_count_at_location.keys)
	        and (betrayal_count_at_location[here] >= generalization_threshold);
	    return base_state + "|" + (risky ? "RISKY" : "SAFE");
	}

	string character_suggested_move(player p) {
		if base_character = "TFT" { return TFT(p); }
		else if base_character = "ALLC" { return ALLC(p); }
		else if base_character = "ALLD" { return ALLD(p); }
		else if base_character = "FTFT" { return FTFT(p); }
		else if base_character = "TF2T" { return TF2T(p); }
		else if base_character = "GRIM" { return GRIM(p); }
		else if base_character = "WSLS" { return WSLS(p); }
		else { return "C"; }
	}

	float effective_anchor_strength(player p) {
		int n <- length(lists_per_other[p]);
		float base <- character_strength * exp(-anchor_decay_rate * n);
		environment_cell here <- environment_cell(location);
		float erosion <- (here != nil) ? (1 - broken_windows_sensitivity * here.disorder) : 1.0;
		erosion <- max(0.0, erosion);
		return max(0.0, min(1.0, base * erosion));
	}

	action init_on_network() {
		current_node <- path_network.vertices closest_to self;
		location <- current_node;
	}

	point weighted_next_node(list<point> candidates) {
		map<point, float> weights <- map<point, float>([]);
		loop c over: candidates {
			environment_cell cell <- environment_cell(c);
			float fb <- (cell != nil and cell in personal_feedback.keys) ? personal_feedback[cell] : 0.0;
			float social <- social_sensitivity > 0 ? social_score(c) : 0.0;
			weights[c] <- exp(sensitivity * fb + social_sensitivity * social);
		}
		return rnd_choice(weights);
	}

	reflex choose_target when: real_env and !well_mixed and (target_node = nil or location = target_node) {
		list<point> neighbors <- list(path_network neighbors_of current_node);
		if empty(neighbors) {
			target_node <- current_node;
		} else {
			target_node <- weighted_next_node(neighbors);
			current_node <- target_node;
		}
	}

	reflex move_on_network when: real_env and !well_mixed and target_node != nil and location != target_node {
		do goto (target:target_node, on:path_network, speed:move_speed);
	}

	reflex wander_fallback when: !real_env and !well_mixed {
		do wander(amplitude:90.0);
	}

	reflex height_decay when: !unlimited_games {
		if height > 0 {
			height <- height - 1;
			score <- score + 1;
		}
	}

	map<environment_cell, float> personal_feedback;

	action update_personal_feedback(environment_cell cell, float value) {
		if cell = nil {
			return;
		}
		float old_val <- (cell in personal_feedback.keys) ? personal_feedback[cell] : 0.0;
		personal_feedback[cell] <- old_val + cell_learning_rate * (value - old_val);
	}

	action update_social_feedback(player opponent, float value) {
		float old_val <- (opponent in social_feedback.keys) ? social_feedback[opponent] : 0.0;
		social_feedback[opponent] <- old_val + social_learning_rate * (value - old_val);
	}

	float social_score(point candidate) {
		float s_s <- 0.0;
		loop p over: social_feedback.keys {
			float pref <- social_feedback[p];
			float dist_now <- current_node distance_to p.location;
			float dist_candidate <- candidate distance_to p.location;
			float normalized_delta <- (dist_now - dist_candidate) / max(1.0, move_speed);
			s_s <- s_s + pref * normalized_delta;
		}
		return s_s / max(1, length(social_feedback));
	}

	map<player, list<string>> lists_per_other;
	map<player, list<string>> my_moves_per_other;

	map<player, map<string, float>> q_d_per_other;
	map<player, map<string, float>> q_c_per_other;
	map<player, string> pending_state;
	map<player, string> pending_action;

	float learning_rate <- 0.1;
	float discount <- 0.9;
	float epsilon <- 0.15;

	// świeży wpis dla partnera - jak dla nowo poznanego (także po zapomnieniu)
	action ensure_partner(player other) {
		if not (other in lists_per_other.keys) {
			lists_per_other[other] <- [];
			my_moves_per_other[other] <- [];
			q_d_per_other[other] <- map<string, float>([]);
			q_c_per_other[other] <- map<string, float>([]);
		}
	}

	// używane w testach: zakłada wpisy dla wszystkich par z udziałem self
	action setup_lists() {
		loop other over: player where (each != self) {
			do ensure_partner(other);
			ask other { do ensure_partner(myself); }
		}
	}

	// Moduł 1: odśwież partnera na końcu LRU; przy przekroczeniu limitu zapomnij najdawniej widzianego.
	// Zapominanie jednostronne: other nadal pamięta self.
	action touch_partner(player other) {
		remove other from: known_others;
		known_others <+ other;
		last_met_cycle[other] <- cycle;
		if dunbar_limit > 0 {
			loop while: length(known_others) > dunbar_limit {
				do forget_partner(first(known_others));
			}
		}
	}

	// usuwa partnera ze WSZYSTKICH map indeksowanych przeciwnikiem;
	// pamięć miejsc (personal_feedback, betrayal_count_at_location) zostaje
	action forget_partner(player other) {
		remove other from: known_others;
		remove key: other from: lists_per_other;
		remove key: other from: my_moves_per_other;
		remove key: other from: q_c_per_other;
		remove key: other from: q_d_per_other;
		remove key: other from: pending_state;
		remove key: other from: pending_action;
		remove key: other from: social_feedback;
		remove key: other from: history_offset;
		nb_forgotten <- nb_forgotten + 1;
		nb_forgets_total <- nb_forgets_total + 1;
	}

	int distinct_partners_in_window() {
		int since <- cycle - partner_window;
		// przycinanie starych wpisów trzyma mapę małą
		loop k over: copy(last_met_cycle.keys) {
			if last_met_cycle[k] < since { remove key: k from: last_met_cycle; }
		}
		return length(last_met_cycle);
	}

	// nowy stan zawsze startuje z priorem initial_cooperation_bias - niezależnie od tego,
	// czy pierwszy raz pojawia się w QLEARN, czy jako next_s w update_q
	action ensure_q_state(player opponent, string s) {
		if not (s in q_d_per_other[opponent].keys) {
			q_d_per_other[opponent][s] <- (1 - initial_cooperation_bias);
			q_c_per_other[opponent][s] <- initial_cooperation_bias;
		}
	}

	action update_q(player opponent, float reward) {
		string s <- pending_state[opponent];
		string a <- pending_action[opponent];

		float old_q <- (a = "D") ? q_d_per_other[opponent][s] : q_c_per_other[opponent][s];

		string next_s <- get_state(opponent);
		do ensure_q_state(opponent, next_s);

		float max_next_q <- max(q_d_per_other[opponent][next_s], q_c_per_other[opponent][next_s]);

		float social_pref <- (opponent in social_feedback.keys) ? social_feedback[opponent] : 0.0;
		float effective_lr <- learning_rate * (1 + social_learning_boost * social_pref);
		effective_lr <- max(0.01, min(0.99, effective_lr));

		float new_q <- old_q + effective_lr * (reward + discount * max_next_q - old_q);

		if a = "D" {
			q_d_per_other[opponent][s] <- new_q;
		} else {
			q_c_per_other[opponent][s] <- new_q;
		}
	}

//	reflex debug_qtable when: character = "QLEARN" and every(50) {
//		write name + " Q-table snapshot:";
//		loop p over: q_c_per_other.keys {
//			loop s over: q_c_per_other[p].keys {
//				write "  vs " + p.name + " state=" + s + " D=" + q_c_per_other[p][s] + " C=" + q_d_per_other[p][s];
//			}
//		}
//	}

//	string get_state(player p) {
//		if lists_per_other[p] = [] {
//			return "START";
//		}
//		string my_last <- last(my_moves_per_other[p]);
//		string opp_last <- last(lists_per_other[p]);
//		return my_last + "|" + opp_last;
//	}

	string strategy(player p) {
		if not unlimited_games and height != 0 { return nil; }
		string base_move;
		if character = "TFT" { base_move <- TFT(p); }
		else if character = "ALLC" { base_move <- ALLC(p); }
		else if character = "ALLD" { base_move <- ALLD(p); }
		else if character = "FTFT" { base_move <- FTFT(p); }
		else if character = "TF2T" { base_move <- TF2T(p); }
		else if character = "GRIM" { base_move <- GRIM(p); }
		else if character = "WSLS" { base_move <- WSLS(p); }
		else if character = "QLEARN" or character = "AQLEARN" { base_move <- QLEARN(p); }
		else { error "Nieznany charakter: " + character; }

		if base_move = "C" and broken_windows_sensitivity > 0 {
		    environment_cell here <- environment_cell(location);
		    float local_disorder <- (here != nil) ? here.disorder : 0.0;
		    if flip(min(0.9, broken_windows_sensitivity * local_disorder)) {
		        base_move <- "D";
		    }
		}

		if (character = "QLEARN" or character = "AQLEARN") and (p in pending_action.keys) {
		    pending_action[p] <- base_move;   // domknięcie: pending_action = to, co naprawdę zagrano
		}

		return base_move;
	}



//	string strategy(player p) {
//		if not unlimited_games and height != 0 {
//			return nil;
//		}
//		if character = "TFT" {
//			return TFT(p);
//		} else if character = "ALLC" {
//			return ALLC(p);
//		} else if character = "ALLD" {
//			return ALLD(p);
//		} else if character = "FTFT" {
//			return FTFT(p);
//		} else if character = "TF2T" {
//			return TF2T(p);
//		} else if character = "GRIM" {
//			return GRIM(p);
//		} else if character = "WSLS" {
//			return WSLS(p);
//		} else if character = "QLEARN" or character = "AQLEARN"{
//			return QLEARN(p);
//		} else {
//			error "Nieznany charakter: " + character;
//		}
//	}

	string TFT(player p) {
		if lists_per_other[p] = [] {
			if classic_start_cooperate { return "C"; }
			return flip(0.5) ? "C" : "D";
		}
		if last(lists_per_other[p]) = "C" {
			return "C";
		}
		return "D";
	}

	string ALLD(player p) {
		return "D";
	}

	string ALLC(player p) {
		return "C";
	}

	string FTFT(player p) {
		if lists_per_other[p] = [] {
			return "C";
		}
		if last(lists_per_other[p]) = "C" {
			return "C";
		}
		if last(lists_per_other[p]) = "D" and flip(forgiveness){
			return "C";
		}
		return "D";
	}

	string TF2T(player p) {
		if lists_per_other[p] = [] {
			if classic_start_cooperate { return "C"; }
			return flip(0.5) ? "C" : "D";
		}
		if last(2, lists_per_other[p]) != ["D","D"] {
			return "C";
		}
		return "D";
	}

	string GRIM(player p) {
		int since <- (p in history_offset.keys) ? history_offset[p] : 0;
		if since = 0 {
			return (lists_per_other[p] contains "D") ? "D" : "C";
		}
		// po przejęciu charakteru: tylko ruchy od przejęcia
		list<string> h <- lists_per_other[p];
		return (copy_between(h, since, length(h)) contains "D") ? "D" : "C";
	}

	string WSLS(player p) {
		if lists_per_other[p] = [] {
			if classic_start_cooperate { return "C"; }
			return flip(0.5) ? "C" : "D";
		}
		string my_last <- last(my_moves_per_other[p]);
		string enemy_last <- last(lists_per_other[p]);

		if enemy_last = "C" {
			return my_last;
		}
		return (my_last = "C") ? "D" : "C";
	}

	// Uwaga: przy obecnej częstości spotkań (kilkanaście-kilkadziesiąt gier na parę) tablice Q per przeciwnik
	// prawie nie odchodzą od prioru - zob. docs/gamadays.md, sekcja "Diagnostyka"
	string QLEARN(player p) {
		string s <- get_state(p);
		do ensure_q_state(p, s);

		environment_cell here <- environment_cell(location);
		float env_fb <- (here != nil and here in personal_feedback.keys) ? personal_feedback[here] : 0.0;

		float adjusted_q_d <- q_d_per_other[p][s] - env_influence * env_fb;
		float adjusted_q_c <- q_c_per_other[p][s] + env_influence * env_fb;

		string action_chosen;
		if flip(epsilon) {
			action_chosen <- flip(0.5) ? "D" : "C";
		} else if adjusted_q_d = adjusted_q_c {
			action_chosen <- flip(0.5) ? "D" : "C";   // remis rozstrzygany losowo, nie na korzyść D
		} else {
			action_chosen <- (adjusted_q_d > adjusted_q_c) ? "D" : "C";
		}

		if character_strength > 0 {
			float pull <- effective_anchor_strength(p);
			if flip(pull) {
				action_chosen <- character_suggested_move(p);
			}
		}

		pending_state[p] <- s;
		pending_action[p] <- action_chosen;

		return action_chosen;
	}

	reflex do_you_wanna_play when: unlimited_games or height = 0 {
		do try_play();
	}

	action try_play() {
		// sąsiedzi liczeni raz na krok (wcześniej dwukrotnie przez atrybut funkcyjny) - te same wartości
		list<player> nearby <- well_mixed ? (list(player) - self) : ((player at_distance(vision_radius)) - [self]);
		if !empty(nearby) {
			enemy <- one_of(nearby);

			if enemy != nil and (unlimited_games or enemy.height = 0) {

				player a <- self;
				player b <- enemy;

				string key <- world.pair_key(a,b);

				if !(key in world.active_pairs.keys) {
					point pn1 <- self.location;
					point pn2 <- enemy.location;

					create game(p1:a,p2:b,location:(pn1 + pn2) / 2, pair_key:key) returns: new_games;

					world.active_pairs[key] <- first(new_games);
				}
			}
		}
	}

	rgb social_link_color(float v) {
		if v > 0 {
			return rgb(0, 255 * min(1.0, v), 0);
		} else {
			return rgb(255 * min(1.0, -v), 0, 0);
		}
	}

	action draw_own_social_links() {
		list<player> candidates <- social_feedback.keys where (abs(social_feedback[each]) > social_link_threshold);
		list<player> sorted_candidates <- candidates sort_by (-abs(social_feedback[each]));
		list<player> top <- first(3, sorted_candidates);

		loop p over: top {
			float v <- social_feedback[p];
			draw line([location, p.location]) color: social_link_color(v) width: 1 + 3 * abs(v);
		}
	}

	aspect social_links_all {
		if show_social_links {
			do draw_own_social_links();
		}
	}

	aspect social_links_selected {
		if show_social_links and self = world.selected_player() {
			do draw_own_social_links();
		}
	}

	aspect cone{
		draw cylinder(10, world.normalized_visual_height(self)) color: (self = world.selected_player() ? #blue : #black);
	}
}

experiment PD type: gui {
	/** Insert here the definition of the input and output of the model */
	parameter "Wybrany agent (indeks)" var: selected_index min: 0 category: "Podgląd pamięci";
	parameter "Pokaż linie relacji społecznych" var: show_social_links category: "Podgląd pamięci";
	parameter "Próg rysowania linii" var: social_link_threshold category: "Podgląd pamięci";

	parameter "Ilość agentów QLEARN" var: nb_QLEARN min: 0 category: "Ilości agentów";
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN min: 0 category: "Ilości agentów";
	parameter "Ilość agentów TFT" var: nb_TFT min: 0 category: "Ilości agentów";
	parameter "Ilość agentów FTFT" var: nb_FTFT min: 0 category: "Ilości agentów";
	parameter "Ilość agentów TF2T" var: nb_TF2T min: 0 category: "Ilości agentów";
	parameter "Ilość agentów GRIM" var: nb_GRIM min: 0 category: "Ilości agentów";
	parameter "Ilość agentów ALLC" var: nb_ALLC min: 0 category: "Ilości agentów";
	parameter "Ilość agentów ALLD" var: nb_ALLD min: 0 category: "Ilości agentów";
	parameter "Ilość agentów WSLS" var: nb_WSLS min: 0 category: "Ilości agentów";

	parameter "Prawdziwe środowisko" var: real_env category: "Środowisko";
	parameter "Ograniczenie rozgrywania gier" var: unlimited_games category: "Środowisko";
	parameter "Rozmiar świata (działa przy sztucznym środowisku)" var: world_size min: 0 category: "Środowisko";
	parameter "Kolumny siatki" var: grid_cols min: 0 category: "Środowisko";
	parameter "Wiersze siatki" var: grid_rows min: 0 category: "Środowisko";
	parameter "Zasięg widzenia" var: vision_radius category: "Środowisko";
	parameter "Czułość ruchu (środowisko)" var: movement_sensitivity category: "Środowisko";
	parameter "Wpływ środowiska na decyzję QLEARN" var: env_influence_qlearn category: "Środowisko";
	parameter "Czułość społeczna AQLEARN" var: social_sensitivity_aqlearn category: "Środowisko";
	parameter "Wzmocnienie uczenia społecznego AQLEARN" var: social_learning_boost_aqlearn category: "Środowisko";
	parameter "Czułość na rozbitą szybę" var: broken_windows_sensitivity min: 0.0 category: "Środowisko";
	parameter "Disorder ograniczony do [0, 1]" var: disorder_clamp category: "Środowisko";

	parameter "Typ gry" var: game_type among: ["PD", "weak_PD", "snowdrift"] category: "Gra";
	parameter "T (pokusa)" var: payoff_T category: "Gra";
	parameter "R (nagroda)" var: payoff_R category: "Gra";
	parameter "P (kara)" var: payoff_P category: "Gra";
	parameter "S (frajer)" var: payoff_S category: "Gra";
	parameter "TFT/TF2T/WSLS zaczynają od C" var: classic_start_cooperate category: "Gra";

	parameter "Limit Dunbara (0 = brak)" var: dunbar_limit min: 0 category: "Moduł 1 – Dunbar";
	parameter "Okno metryki partnerów (cykle)" var: partner_window min: 1 category: "Moduł 1 – Dunbar";

	parameter "Ewolucja strategii" var: evolution_on category: "Moduł 2 – ewolucja";
	parameter "Co ile cykli" var: evolution_interval min: 1 category: "Moduł 2 – ewolucja";
	parameter "Szum selekcji K (Fermi)" var: fermi_k min: 0.001 category: "Moduł 2 – ewolucja";
	parameter "Prawdopodobieństwo mutacji" var: mutation_rate min: 0.0 max: 1.0 category: "Moduł 2 – ewolucja";
	parameter "Populacja dobrze wymieszana (bez przestrzeni)" var: well_mixed category: "Moduł 2 – ewolucja";
	parameter "Rdzeń zgodności (compat_core)" var: compat_core category: "Etap 1 – zgodność";
	parameter "Liczebność rdzenia N" var: compat_N min: 2 category: "Etap 1 – zgodność";
	parameter "Skład rdzenia" var: compat_mix among: ["equal", "tft_alld"] category: "Etap 1 – zgodność";
	parameter "Macierz wypłat" var: payoff_preset among: ["custom", "PD_classic", "weak_PD", "snowdrift"] category: "Etap 1 – zgodność";
	parameter "Eksport compat_results.csv" var: compat_export category: "Etap 1 – zgodność";
	parameter "Eksport szeregów czasowych" var: timeseries_export category: "Diagnostyka";
	parameter "Co ile cykli próbka" var: sample_interval min: 1 category: "Diagnostyka";

	parameter "Pomiar czasu cyklu" var: perf_log category: "Diagnostyka";
	parameter "Okno pomiaru (cykle)" var: perf_interval min: 1 category: "Diagnostyka";
	parameter "Eksport odcisku regresyjnego" var: regression_export category: "Diagnostyka";
	parameter "Cykl odcisku" var: regression_cycle min: 1 category: "Diagnostyka";

	output {
		display abc {
			species environment_cell aspect: summary;
			species park_boundary aspect: default transparency: 0.3;
			species path_segment aspect: default;
			species player aspect: social_links_all;
			species player aspect: cone;

			//species game aspect: default;
		}
		display chart type: 2d{
			chart "Score" type: series{
				loop p_s over: player{
					data "" + p_s + p_s.character + " score" value: p_s.for_chart;
				}
			}
		}
		display ewolucja type: 2d refresh: every(10 #cycle) {
			chart "Udziały charakterów" type: series {
				loop ch over: characters {
					data ch value: world.share_of(ch);
				}
			}
		}
		display dunbar type: 2d refresh: every(10 #cycle) {
			chart "Pamięć partnerów" type: series {
				data "średnio znanych partnerów" value: world.mean_known_partners();
				data "różni partnerzy w oknie" value: world.mean_distinct_partners_window();
				data "zapomnienia / cykl" value: forgets_last_cycle;
			}
		}
		display agent_memory {
			species environment_cell aspect: personal;
			species park_boundary aspect: default transparency: 0.3;
			species path_segment aspect: default;
			species player aspect: social_links_selected;
			species player aspect: cone;


			overlay position: {10, 10} size: {250 #px, 40 #px} background: #white transparency: 0.3 {
				draw "Agent #" + string(selected_index) +
					(world.selected_player() != nil ? " (" + world.selected_player().character + ")" : "")
					at: {10#px, 20#px} color: #black font: font("Arial", 12, #bold);

			}
		}
	}
}

experiment A_baseline type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
	parameter "variant_name" var: variant_name init: "A_baseline";
	parameter "log_games" var: log_games init: false;
	parameter "Ilość agentów QLEARN" var: nb_QLEARN init: 20;
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN init: 0;
	parameter "movement_sensitivity" var: movement_sensitivity init: 0.0;
	parameter "env_influence_qlearn" var: env_influence_qlearn init: 0.0;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 0.0;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 0.0;
}

experiment B_env_movement type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
	parameter "variant_name" var: variant_name init: "B_env_movement";
	parameter "log_games" var: log_games init: false;
	parameter "Ilość agentów QLEARN" var: nb_QLEARN init: 20;
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN init: 0;
	parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
	parameter "env_influence_qlearn" var: env_influence_qlearn init: 0.0;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 0.0;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 0.0;
}

experiment C_social_movement type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
	parameter "variant_name" var: variant_name init: "C_social_movement";
	parameter "log_games" var: log_games init: false;
	parameter "Ilość agentów QLEARN" var: nb_QLEARN init: 0;
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN init: 20;
	parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
	parameter "env_influence_qlearn" var: env_influence_qlearn init: 0.0;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 1.5;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 0.0;
}

experiment D_social_learning type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
	parameter "variant_name" var: variant_name init: "D_social_learning";
	parameter "log_games" var: log_games init: false;
	parameter "Ilość agentów QLEARN" var: nb_QLEARN init: 0;
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN init: 20;
	parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
	parameter "env_influence_qlearn" var: env_influence_qlearn init: 0.0;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 1.5;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 2.0;
}

experiment E1_classic_TFT type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
    parameter "variant_name" var: variant_name init: "E1_classic_TFT";
    parameter "log_games" var: log_games init: false;
    parameter "Ilość agentów TFT" var: nb_TFT init: 20;
    parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
}

experiment E2_classic_WSLS type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
    parameter "variant_name" var: variant_name init: "E2_classic_WSLS";
    parameter "log_games" var: log_games init: false;
    parameter "Ilość agentów WSLS" var: nb_WSLS init: 20;
    parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
}

experiment E3_classic_GRIM type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
    parameter "variant_name" var: variant_name init: "E3_classic_GRIM";
    parameter "log_games" var: log_games init: false;
    parameter "Ilość agentów GRIM" var: nb_GRIM init: 20;
    parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
}

experiment F_broken_windows_anchor type: batch repeat: 30 until: cycle > end_cycle keep_seed: false {
	parameter "variant_name" var: variant_name init: "F_broken_windows_anchor";
	parameter "log_games" var: log_games init: false;
	parameter "Ilość agentów AQLEARN" var: nb_AQLEARN init: 20;
	parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 1.5;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 2.0;
	parameter "broken_windows_sensitivity" var: broken_windows_sensitivity init: 0.4;
	parameter "base_character_qlearn" var: base_character_qlearn init: "TFT";
	parameter "character_strength_qlearn" var: character_strength_qlearn init: 0.6;
}

// ===== Etap 1: walidacja pojedyncza (rdzeń + kontrola well_mixed) =====
// P1 i P2 oceniane na tych samych przebiegach (ewolucja, mutation_rate 0 vs 0,01), P3 bez ewolucji (80% TFT + 20% ALLD).
// Wiersz compat_results.csv = przebieg; werdykty liczy web/stage1.py --verdict.
experiment S1_P12_space type: batch repeat: 15 keep_seed: true until: cycle > end_cycle {
	float seed <- 20261123.0;
	parameter "variant_name" var: variant_name init: "S1_P12_space";
	parameter "prediction" var: prediction init: "P1P2";
	parameter "log_games" var: log_games init: false;
	parameter "compat_core" var: compat_core init: true;
	parameter "compat_export" var: compat_export init: true;
	parameter "compat_mix" var: compat_mix init: "equal";
	parameter "evolution_on" var: evolution_on init: true;
	parameter "well_mixed" var: well_mixed init: false;
	parameter "end_cycle" var: end_cycle init: 20000;
	parameter "vision_radius" var: vision_radius init: 30;
	parameter "partner_window" var: partner_window init: 1000000000;
	parameter "mutation_rate" var: mutation_rate among: [0.0, 0.01];
	parameter "payoff_preset" var: payoff_preset among: ["PD_classic", "weak_PD", "snowdrift"];
	parameter "compat_N" var: compat_N among: [200, 500];
}

experiment S1_P12_wellmixed type: batch repeat: 15 keep_seed: true until: cycle > end_cycle {
	float seed <- 20261123.0;
	parameter "variant_name" var: variant_name init: "S1_P12_wellmixed";
	parameter "prediction" var: prediction init: "P1P2";
	parameter "log_games" var: log_games init: false;
	parameter "compat_core" var: compat_core init: true;
	parameter "compat_export" var: compat_export init: true;
	parameter "compat_mix" var: compat_mix init: "equal";
	parameter "evolution_on" var: evolution_on init: true;
	parameter "well_mixed" var: well_mixed init: true;
	parameter "end_cycle" var: end_cycle init: 20000;
	parameter "vision_radius" var: vision_radius init: 30;
	parameter "partner_window" var: partner_window init: 1000000000;
	parameter "mutation_rate" var: mutation_rate among: [0.0, 0.01];
	parameter "payoff_preset" var: payoff_preset among: ["PD_classic", "weak_PD", "snowdrift"];
	parameter "compat_N" var: compat_N among: [200, 500];
}

experiment S1_P3_space type: batch repeat: 15 keep_seed: true until: cycle > end_cycle {
	float seed <- 20261123.0;
	parameter "variant_name" var: variant_name init: "S1_P3_space";
	parameter "prediction" var: prediction init: "P3";
	parameter "log_games" var: log_games init: false;
	parameter "compat_core" var: compat_core init: true;
	parameter "compat_export" var: compat_export init: true;
	parameter "compat_mix" var: compat_mix init: "tft_alld";
	parameter "evolution_on" var: evolution_on init: false;
	parameter "well_mixed" var: well_mixed init: false;
	parameter "end_cycle" var: end_cycle init: 20000;
	parameter "vision_radius" var: vision_radius init: 30;
	parameter "partner_window" var: partner_window init: 1000000000;
	parameter "dunbar_limit" var: dunbar_limit among: [0, 5, 15, 50];
	parameter "payoff_preset" var: payoff_preset among: ["PD_classic", "weak_PD", "snowdrift"];
	parameter "compat_N" var: compat_N among: [200, 500];
}

experiment S1_P3_wellmixed type: batch repeat: 15 keep_seed: true until: cycle > end_cycle {
	float seed <- 20261123.0;
	parameter "variant_name" var: variant_name init: "S1_P3_wellmixed";
	parameter "prediction" var: prediction init: "P3";
	parameter "log_games" var: log_games init: false;
	parameter "compat_core" var: compat_core init: true;
	parameter "compat_export" var: compat_export init: true;
	parameter "compat_mix" var: compat_mix init: "tft_alld";
	parameter "evolution_on" var: evolution_on init: false;
	parameter "well_mixed" var: well_mixed init: true;
	parameter "end_cycle" var: end_cycle init: 20000;
	parameter "vision_radius" var: vision_radius init: 30;
	parameter "partner_window" var: partner_window init: 1000000000;
	parameter "dunbar_limit" var: dunbar_limit among: [0, 5, 15, 50];
	parameter "payoff_preset" var: payoff_preset among: ["PD_classic", "weak_PD", "snowdrift"];
	parameter "compat_N" var: compat_N among: [200, 500];
}

// Test regresyjny nr 1: uruchom na tym commicie (baza) i po każdej zmianie; wiersze
// regression_fingerprint.csv muszą być identyczne. Populacja celowo włącza wszystkie mechanizmy JASSS.
experiment R0_regression type: batch repeat: 3 keep_seed: true until: cycle > regression_cycle {
	float seed <- 20261123.0;
	parameter "variant_name" var: variant_name init: "R0_regression";
	parameter "log_games" var: log_games init: false;
	parameter "regression_export" var: regression_export init: true;
	parameter "regression_cycle" var: regression_cycle init: 2000;
	parameter "unlimited_games" var: unlimited_games among: [false, true];
	parameter "nb_QLEARN" var: nb_QLEARN init: 6;
	parameter "nb_AQLEARN" var: nb_AQLEARN init: 6;
	parameter "nb_TFT" var: nb_TFT init: 2;
	parameter "nb_ALLC" var: nb_ALLC init: 2;
	parameter "nb_ALLD" var: nb_ALLD init: 2;
	parameter "nb_FTFT" var: nb_FTFT init: 2;
	parameter "nb_TF2T" var: nb_TF2T init: 2;
	parameter "nb_GRIM" var: nb_GRIM init: 2;
	parameter "nb_WSLS" var: nb_WSLS init: 2;
	parameter "movement_sensitivity" var: movement_sensitivity init: 2.0;
	parameter "env_influence_qlearn" var: env_influence_qlearn init: 0.5;
	parameter "social_sensitivity_aqlearn" var: social_sensitivity_aqlearn init: 1.5;
	parameter "social_learning_boost_aqlearn" var: social_learning_boost_aqlearn init: 2.0;
	parameter "broken_windows_sensitivity" var: broken_windows_sensitivity init: 0.4;
	parameter "character_strength_qlearn" var: character_strength_qlearn init: 0.6;
}

experiment test_disorder_decay type: test {
    test "disorder zanika geometrycznie z disorder_decay" {
        environment_cell c <- first(environment_cell);
        ask c { disorder <- 1.0; }
        loop times: 10 {
            ask c { do apply_decay(); }
        }
        float expected <- 1.0 * (disorder_decay ^ 10);
        assert abs(c.disorder - expected) < 0.001;
    }
}

experiment test_disorder_bump_asymmetry type: test {
    test "D-D podbija disorder mocniej niż D-C, C-C nie podbija wcale" {
        // disorder_bump_for jest tą samą funkcją, której używa game.init
        assert world.disorder_bump_for("D", "D") = disorder_bump_dd;
        assert world.disorder_bump_for("D", "C") = disorder_bump_d;
        assert world.disorder_bump_for("C", "D") = disorder_bump_d;
        assert world.disorder_bump_for("C", "C") = 0.0;
        assert world.disorder_bump_for("D", "D") > world.disorder_bump_for("D", "C");
    }
}

experiment test_broken_windows_affects_classic type: test {
    test "ALLC defektuje częściej przy wysokim disorder niż przy zerowym" {
        broken_windows_sensitivity <- 0.5;
        create player(character:"ALLC") number: 1;
        player p <- first(player);
        environment_cell here <- environment_cell(p.location);

        ask here { disorder <- 0.0; }
        int d_count_low <- 0;
        loop times: 1000 { if p.strategy(p) = "D" { d_count_low <- d_count_low + 1; } }

        ask here { disorder <- 1.0; }
        int d_count_high <- 0;
        loop times: 1000 { if p.strategy(p) = "D" { d_count_high <- d_count_high + 1; } }

        assert d_count_low = 0; // ALLC bez disorder nigdy nie defektuje
        assert d_count_high > 400; // przy disorder=1.0, sensitivity=0.5 -> ~50% D
    }
}

experiment test_reputation_state_dimension type: test {
    test "get_state zwraca RISKY dopiero po przekroczeniu progu" {
        generalization_threshold <- 3;
        create player number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }
        environment_cell here <- environment_cell(p.location);

        assert (p.get_state(opp) contains "SAFE");

        ask p { do register_betrayal(here); } // 1
        assert (p.get_state(opp) contains "SAFE");

        ask p { do register_betrayal(here); } // 2
        assert (p.get_state(opp) contains "SAFE");

        ask p { do register_betrayal(here); } // 3 = próg
        assert (p.get_state(opp) contains "RISKY");
    }
}

experiment test_anchor_decay type: test {
    test "effective_anchor_strength maleje wykładniczo z liczbą interakcji" {
        broken_windows_sensitivity <- 0.0; // wyłącz erozję środowiskową na czas testu
        anchor_decay_rate <- 0.15;
        create player(character:"QLEARN", character_strength:0.8) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }

        float s0 <- p.effective_anchor_strength(opp); // n=0
        assert abs(s0 - 0.8) < 0.001; // exp(0) = 1, brak erozji -> pełna siła

        loop times: 5 { p.lists_per_other[opp] <+ "C"; } // symuluj 5 interakcji
        float s5 <- p.effective_anchor_strength(opp);
        float expected <- 0.8 * exp(-0.15 * 5);
        assert abs(s5 - expected) < 0.001;
        assert s5 < s0; // musi maleć
    }
}

experiment test_anchor_erosion_by_disorder type: test {
    test "wysoki disorder obniża effective_anchor_strength do zera" {
        anchor_decay_rate <- 0.0;
        create player(character:"QLEARN", character_strength:0.8) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }
        environment_cell here <- environment_cell(p.location);

        broken_windows_sensitivity <- 2.0; // celowo mocne, by wymusić erozję do 0
        ask here { disorder <- 1.0; }

        float s <- p.effective_anchor_strength(opp);
        assert s = 0.0; // erosion = 1 - 2.0*1.0 = -1 -> max(0, ...) = 0 -> wynik 0
    }
}

experiment test_pending_action_sync type: test {
    test "pending_action zgadza się z faktycznie zagranym ruchem mimo override kotwicy" {
        anchor_decay_rate <- 0.0;
        broken_windows_sensitivity <- 0.0;
        create player(character: "QLEARN", base_character: "ALLD", character_strength: 1.0, epsilon: 0.0) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }

        string played <- p.QLEARN(opp);
        assert played = "D";
        assert p.pending_action[opp] = played;
    }
}

experiment test_pending_action_sync_broken_windows type: test {
    test "pending_action zgadza się z ruchem po override rozbitej szyby" {
        create player(character: "QLEARN", character_strength: 0.0, epsilon: 0.0, initial_cooperation_bias: 1.0) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }
        environment_cell here <- environment_cell(p.location);

        broken_windows_sensitivity <- 1.0;
        ask here { disorder <- 1.0; }

        bool found_mismatch <- false;
        loop times: 200 {
            string played <- p.strategy(opp);
            if p.pending_action[opp] != played {
                found_mismatch <- true;
                break;
            }
        }
        assert not found_mismatch;
    }
}

experiment test_anchor_not_applied_to_classic type: test {
    test "character_strength pozostaje 0.0 dla agentów klasycznych mimo globalnego parametru" {
        character_strength_qlearn <- 0.9;
        create player(character: "TFT") number: 1 returns: classic;
        create player(character: "QLEARN") number: 1 returns: learners;
        // ta sama akcja, którą wywołuje global.init
        ask classic { do apply_character_params(); }
        ask learners { do apply_character_params(); }
        assert first(classic).character_strength = 0.0;
        assert first(learners).character_strength = 0.9; // kontrola: parametr faktycznie trafia do QLEARN
    }
}

experiment test_disorder_persists_not_just_noise type: test {
    test "powtarzana defekcja w jednym miejscu utrzymuje disorder powyżej poziomu bazowego" {
        environment_cell hot <- environment_cell(0);
        environment_cell cold <- environment_cell(49); // odległa komórka, bez żadnej defekcji
        ask hot { disorder <- 0.0; }
        ask cold { disorder <- 0.0; }

        // symuluj 20 cykli: co 5 cykli nowa defekcja w "hot", nic w "cold"
        loop times: 20 {
            ask hot { disorder <- disorder + disorder_bump_dd; }
            ask hot { do apply_decay(); }
            ask cold { do apply_decay(); }
        }

        assert hot.disorder > cold.disorder;
        assert hot.disorder > 0.3; // nie zdążyło zaniknąć do szumu bliskiego zeru
    }
}

experiment test_reputation_creates_self_fulfilling_bias type: test {
    test "RISKY zmienia zachowanie mimo dobrej historii z akurat tym przeciwnikiem" {
        generalization_threshold <- 3;
        broken_windows_sensitivity <- 0.0;
        create player(character: "QLEARN", epsilon: 0.0, character_strength: 0.0, env_influence: 0.0) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }
        environment_cell here <- environment_cell(p.location);

        loop times: 10 {
            p.lists_per_other[opp] <+ "C";
            p.my_moves_per_other[opp] <+ "C";
        }

        // z tym przeciwnikiem w stanie C|C opłaca się kooperować,
        // ale w "ryzykownym" miejscu agent nauczył się (na innych) defektować
        ask p {
            q_c_per_other[opp]["C|C|SAFE"] <- 5.0;
            q_d_per_other[opp]["C|C|SAFE"] <- 1.0;
            q_c_per_other[opp]["C|C|RISKY"] <- 0.0;
            q_d_per_other[opp]["C|C|RISKY"] <- 3.0;
        }

        assert p.get_state(opp) = "C|C|SAFE";
        assert p.QLEARN(opp) = "C";

        ask p { do register_betrayal(here); }
        ask p { do register_betrayal(here); }
        ask p { do register_betrayal(here); }

        assert p.get_state(opp) = "C|C|RISKY";
        assert p.QLEARN(opp) = "D"; // ta sama historia z opp, inna decyzja - przez reputację miejsca
    }
}

experiment test_new_state_uses_cooperation_bias type: test {
    test "stan odkryty w update_q dostaje prior initial_cooperation_bias, a nie 0/0" {
        broken_windows_sensitivity <- 0.0;
        create player(character: "QLEARN", epsilon: 0.0, character_strength: 0.0, initial_cooperation_bias: 0.8) number: 2;
        player p <- player[0];
        player opp <- player[1];
        ask p { do setup_lists(); }

        string played <- p.QLEARN(opp); // stan START
        p.lists_per_other[opp] <+ "C";
        p.my_moves_per_other[opp] <+ played;
        ask p { do update_q(opp, payoff_R); }

        string next_s <- p.get_state(opp);
        assert abs(p.q_c_per_other[opp][next_s] - 0.8) < 0.001;
        assert abs(p.q_d_per_other[opp][next_s] - 0.2) < 0.001;
    }

    test "remis Q_D = Q_C rozstrzygany losowo, a nie zawsze na D" {
        broken_windows_sensitivity <- 0.0;
        create player(character: "QLEARN", epsilon: 0.0, character_strength: 0.0, initial_cooperation_bias: 0.5) number: 2 returns: pair;
        player p <- pair[0];
        player opp <- pair[1];
        ask p { do setup_lists(); }

        int c_count <- 0;
        loop times: 1000 { if p.QLEARN(opp) = "C" { c_count <- c_count + 1; } }
        assert c_count > 400 and c_count < 600;
    }
}

experiment test_anchor_shifts_early_behavior type: test {
    test "silna kotwica ALLC zwiększa kooperację względem braku kotwicy, przy identycznym Q-learningu w tle" {
        anchor_decay_rate <- 0.15;
        broken_windows_sensitivity <- 0.0;

        create player(character: "QLEARN", base_character: "ALLC", character_strength: 0.9,
                       epsilon: 0.0, initial_cooperation_bias: 0.1) number: 1 returns: with_anchor;
        create player(character: "QLEARN", base_character: "ALLC", character_strength: 0.0,
                       epsilon: 0.0, initial_cooperation_bias: 0.1) number: 1 returns: without_anchor;
        create player number: 1 returns: opps;

        player pa <- first(with_anchor);
        player pb <- first(without_anchor);
        player opp <- first(opps);
        ask pa { do setup_lists(); }
        ask pb { do setup_lists(); }

        int c_count_a <- 0;
        int c_count_b <- 0;
        loop times: 100 {
            if pa.QLEARN(opp) = "C" { c_count_a <- c_count_a + 1; }
            if pb.QLEARN(opp) = "C" { c_count_b <- c_count_b + 1; }
        }

        assert c_count_a > c_count_b;
    }
}

experiment test_payoff_validation type: test {
    test "walidacja macierzy zależy od game_type" {
        game_type <- "PD";
        payoff_T <- 9.0; payoff_R <- 5.0; payoff_P <- 1.0; payoff_S <- 0.0;
        assert world.payoffs_valid();
        assert world.payoffs_integer();

        game_type <- "weak_PD";
        assert not world.payoffs_valid();   // P > S - to nie jest słaby PD
        payoff_T <- 1.6; payoff_R <- 1.0; payoff_P <- 0.0; payoff_S <- 0.0;
        assert world.payoffs_valid();
        assert not world.payoffs_integer();

        game_type <- "snowdrift";
        assert not world.payoffs_valid();
        payoff_T <- 4.0; payoff_R <- 3.0; payoff_S <- 2.0; payoff_P <- 0.0;
        assert world.payoffs_valid();

        game_type <- "PD";
        assert not world.payoffs_valid();   // snowdrift nie przechodzi jako PD
    }
}

experiment test_classic_start_switch type: test {
    test "classic_start_cooperate: TFT/TF2T/WSLS zaczynają od C; wyłączony - losowo" {
        broken_windows_sensitivity <- 0.0;
        create player(character: "TFT") number: 1 returns: tft;
        create player(character: "TF2T") number: 1 returns: tf2t;
        create player(character: "WSLS") number: 1 returns: wsls;
        create player(character: "ALLC") number: 1 returns: opps;
        player opp <- first(opps);
        ask player { do setup_lists(); }

        classic_start_cooperate <- true;
        int d_on <- 0;
        loop times: 100 {
            if first(tft).strategy(opp) = "D" { d_on <- d_on + 1; }
            if first(tf2t).strategy(opp) = "D" { d_on <- d_on + 1; }
            if first(wsls).strategy(opp) = "D" { d_on <- d_on + 1; }
        }
        assert d_on = 0;

        classic_start_cooperate <- false;
        int d_off <- 0;
        loop times: 100 {
            if first(tft).strategy(opp) = "D" { d_off <- d_off + 1; }
            if first(tf2t).strategy(opp) = "D" { d_off <- d_off + 1; }
            if first(wsls).strategy(opp) = "D" { d_off <- d_off + 1; }
        }
        assert d_off > 100 and d_off < 200;   // ~150 z 300
    }
}

experiment test_lazy_partner_init type: test {
    test "mapy per przeciwnik powstają przy pierwszej grze, bez setup_lists" {
        log_games <- false;
        unlimited_games <- true;
        create player(character: "TFT") number: 2 returns: pair;
        player a <- pair[0];
        player b <- pair[1];
        assert not (b in a.lists_per_other.keys);
        create game(p1: a, p2: b, pair_key: "t") number: 1;
        assert length(a.lists_per_other[b]) = 1;
        assert length(b.lists_per_other[a]) = 1;
        assert a.known_others = [b];
    }
}

experiment test_forget_clears_all_maps type: test {
    test "zapomnienie usuwa partnera ze wszystkich map per przeciwnik (jednostronnie)" {
        log_games <- false;
        unlimited_games <- true;
        broken_windows_sensitivity <- 0.0;
        dunbar_limit <- 0;
        create player(character: "QLEARN") number: 2 returns: pair;
        player a <- pair[0];
        player b <- pair[1];
        ask a { do setup_lists(); }
        create game(p1: a, p2: b, pair_key: "t") number: 1;

        assert b in a.lists_per_other.keys;
        assert b in a.my_moves_per_other.keys;
        assert b in a.q_c_per_other.keys;
        assert b in a.q_d_per_other.keys;
        assert b in a.pending_state.keys;
        assert b in a.pending_action.keys;
        assert b in a.social_feedback.keys;
        assert b in a.known_others;

        ask a { do forget_partner(b); }

        assert not (b in a.lists_per_other.keys);
        assert not (b in a.my_moves_per_other.keys);
        assert not (b in a.q_c_per_other.keys);
        assert not (b in a.q_d_per_other.keys);
        assert not (b in a.pending_state.keys);
        assert not (b in a.pending_action.keys);
        assert not (b in a.social_feedback.keys);
        assert not (b in a.known_others);
        assert a.nb_forgotten = 1;

        assert a in b.lists_per_other.keys;   // b nadal pamięta a
        assert a in b.known_others;
    }
}

experiment test_lru_keeps_most_recent type: test {
    test "LRU zapomina najdawniej widzianego, nigdy ostatniego" {
        log_games <- false;
        unlimited_games <- true;
        broken_windows_sensitivity <- 0.0;
        dunbar_limit <- 2;
        create player(character: "ALLC") number: 4 returns: ps;
        player a <- ps[0];
        player b <- ps[1];
        player c <- ps[2];
        player d <- ps[3];

        create game(p1: a, p2: b, pair_key: "ab1") number: 1;
        create game(p1: a, p2: c, pair_key: "ac1") number: 1;
        assert a.known_others = [b, c];

        create game(p1: a, p2: b, pair_key: "ab2") number: 1;   // b odświeżony
        assert a.known_others = [c, b];

        create game(p1: a, p2: d, pair_key: "ad1") number: 1;   // wypada c, nie b
        assert a.known_others = [b, d];
        assert not (c in a.lists_per_other.keys);
        assert b in a.lists_per_other.keys;
        assert length(a.lists_per_other[b]) = 2;   // historia z b zachowana

        // partner bieżącej gry nigdy nie wypada, nawet przy limicie 1
        dunbar_limit <- 1;
        create game(p1: a, p2: c, pair_key: "ac2") number: 1;
        assert a.known_others = [c];
    }
}

experiment test_anchor_full_after_forget type: test {
    test "po zapomnieniu kotwica wraca do pełnej siły" {
        log_games <- false;
        unlimited_games <- true;
        broken_windows_sensitivity <- 0.0;
        anchor_decay_rate <- 0.15;
        create player(character: "QLEARN", character_strength: 0.8) number: 2 returns: pair;
        player a <- pair[0];
        player b <- pair[1];
        loop i from: 1 to: 5 {
            create game(p1: a, p2: b, pair_key: "ab" + i) number: 1;
        }
        assert a.effective_anchor_strength(b) < 0.8;

        ask a { do forget_partner(b); }
        ask a { do ensure_partner(b); }   // ponowne spotkanie
        assert abs(a.effective_anchor_strength(b) - 0.8) < 0.001;
    }
}

experiment test_pending_action_sync_with_dunbar type: test {
    test "pending_action zgodne z zagranym ruchem przy włączonym limicie i rozbitej szybie" {
        log_games <- false;
        unlimited_games <- true;
        dunbar_limit <- 1;
        broken_windows_sensitivity <- 1.0;
        create player(character: "QLEARN", epsilon: 0.0, initial_cooperation_bias: 1.0) number: 1 returns: learners;
        create player(character: "ALLC") number: 2 returns: opps;
        player a <- first(learners);
        ask environment_cell { disorder <- 0.5; }

        bool mismatch <- false;
        loop i from: 1 to: 50 {
            player opp <- opps[i mod 2];
            create game(p1: a, p2: opp, pair_key: "g" + i) number: 1;
            if a.pending_action[opp] != last(a.my_moves_per_other[opp]) { mismatch <- true; }
            if length(a.known_others) != 1 { mismatch <- true; }
        }
        assert not mismatch;
        assert a.nb_forgotten = 49;   // zmiana partnera co grę przy limicie 1
    }
}

experiment test_disorder_clamp type: test {
    test "disorder_clamp trzyma disorder w [0, 1]; wyłączony - bez limitu" {
        log_games <- false;
        unlimited_games <- true;
        broken_windows_sensitivity <- 0.0;
        create player(character: "ALLD") number: 2 returns: pair;
        player a <- pair[0];
        player b <- pair[1];
        environment_cell cell_a <- environment_cell(a.location);

        disorder_clamp <- true;
        loop i from: 1 to: 20 { create game(p1: a, p2: b, pair_key: "c" + i) number: 1; }
        assert cell_a.disorder <= 1.0;
        assert cell_a.disorder = 1.0;   // 20 x 0.15 przekracza 1, więc dochodzi do sufitu

        disorder_clamp <- false;
        loop i from: 1 to: 20 { create game(p1: a, p2: b, pair_key: "u" + i) number: 1; }
        assert cell_a.disorder > 1.0;
    }
}

experiment test_exploitation_counter type: test {
    test "nb_exploitations liczy tylko gry C-D" {
        log_games <- false;
        unlimited_games <- true;
        broken_windows_sensitivity <- 0.0;
        create player(character: "ALLC") number: 1 returns: cs;
        create player(character: "ALLD") number: 2 returns: ds;
        create game(p1: first(cs), p2: ds[0], pair_key: "cd") number: 1;
        assert nb_exploitations = 1;
        create game(p1: ds[0], p2: ds[1], pair_key: "dd") number: 1;
        assert nb_exploitations = 1;
        assert abs(world.exploitation_rate() - 0.5) < 0.001;
    }
}

experiment test_fermi_rule type: test {
    test "Fermi: π_model >> π_self prawie zawsze imitacja; równe π - ok. 50%" {
        fermi_k <- 0.5;
        mutation_rate <- 0.0;
        create player(character: "ALLC", window_payoff: 0.0, window_games: 10) number: 1 returns: me;
        create player(character: "ALLD", window_payoff: 90.0, window_games: 10) number: 1 returns: rich;
        create player(character: "TFT", window_payoff: 0.0, window_games: 10) number: 1 returns: equal;
        player p <- first(me);

        int adopt_rich <- 0;
        int adopt_equal <- 0;
        loop times: 1000 {
            if p.evolution_choice(first(rich)) = "ALLD" { adopt_rich <- adopt_rich + 1; }
            if p.evolution_choice(first(equal)) = "TFT" { adopt_equal <- adopt_equal + 1; }
        }
        assert adopt_rich > 990;
        assert adopt_equal > 430 and adopt_equal < 570;
        assert abs(world.fermi_probability(3.0, 3.0) - 0.5) < 0.001;
    }

    test "brak imitacji, gdy π nieokreślone albo model spoza evolvable_characters" {
        mutation_rate <- 0.0;
        create player(character: "ALLC", window_payoff: 0.0, window_games: 0) number: 1 returns: idle;
        create player(character: "ALLD", window_payoff: 90.0, window_games: 10) number: 1 returns: rich;
        create player(character: "QLEARN", window_payoff: 90.0, window_games: 10) number: 1 returns: learner;
        create player(character: "ALLC", window_payoff: 0.0, window_games: 10) number: 1 returns: me;
        loop times: 200 {
            assert first(idle).evolution_choice(first(rich)) = "ALLC";
            assert first(me).evolution_choice(first(learner)) = "ALLC";
        }
    }
}

experiment test_mutation_only_evolvable type: test {
    test "mutacja zwraca tylko charaktery z evolvable_characters" {
        mutation_rate <- 1.0;
        evolvable_characters <- ["ALLC", "ALLD"];
        create player(character: "ALLC") number: 1 returns: me;
        bool outside <- false;
        loop times: 500 {
            if !(first(me).evolution_choice(nil) in ["ALLC", "ALLD"]) { outside <- true; }
        }
        assert not outside;
    }
}

experiment test_grim_since_takeover type: test {
    test "GRIM po przejęciu charakteru liczy zdrady tylko od przejęcia; pamięć partnera zostaje" {
        log_games <- false;
        unlimited_games <- true;
        broken_windows_sensitivity <- 0.0;
        create player(character: "TFT") number: 1 returns: me;
        create player(character: "ALLD") number: 1 returns: opps;
        player p <- first(me);
        player opp <- first(opps);
        create game(p1: p, p2: opp, pair_key: "g1") number: 1;   // opp zdradził
        assert p.lists_per_other[opp] contains "D";

        ask p { do change_character("GRIM"); }
        assert p.character = "GRIM";
        assert length(p.lists_per_other[opp]) = 1;   // historia zachowana
        assert p.GRIM(opp) = "C";                     // stara zdrada nie liczy się

        create game(p1: p, p2: opp, pair_key: "g2") number: 1;   // nowa zdrada po przejęciu
        assert p.GRIM(opp) = "D";
    }
}

experiment test_evolution_step type: test {
    test "krok ewolucji: synchroniczny, zeruje okna, nie rusza QLEARN" {
        evolution_on <- true;
        well_mixed <- true;
        fermi_k <- 0.01;
        mutation_rate <- 0.0;
        create player(character: "ALLC", window_payoff: 0.0, window_games: 10) number: 5;
        create player(character: "ALLD", window_payoff: 90.0, window_games: 10) number: 5;
        create player(character: "QLEARN", window_payoff: 0.0, window_games: 10) number: 1 returns: learners;

        ask world { do evolution_step(); }

        assert first(learners).character = "QLEARN";
        assert empty(player where (each.window_games != 0));
        assert length(player where (each.character = "ALLD")) >= 5;
    }
}

experiment test_well_mixed_pairing type: test {
    test "well_mixed: gra z agentem daleko poza zasięgiem widzenia" {
        well_mixed <- true;
        unlimited_games <- true;
        log_games <- false;
        vision_radius <- 1;
        create player(character: "ALLC", location: {0, 0}) number: 1 returns: a;
        create player(character: "ALLC", location: {world.shape.width, world.shape.height}) number: 1 returns: b;
        ask first(a) { do try_play(); }
        assert first(a).nb_games = 1;
    }
}

experiment test_pending_action_sync_all_modules type: test {
    test "pending_action zgodne z ruchem przy włączonych modułach 1-2 i rozbitej szybie" {
        log_games <- false;
        unlimited_games <- true;
        dunbar_limit <- 2;
        evolution_on <- true;
        mutation_rate <- 0.3;
        well_mixed <- true;
        broken_windows_sensitivity <- 1.0;
        create player(character: "QLEARN", epsilon: 0.0, initial_cooperation_bias: 1.0) number: 1 returns: learners;
        create player(character: "ALLC") number: 3 returns: opps;
        player a <- first(learners);
        ask environment_cell { disorder <- 0.5; }

        bool mismatch <- false;
        loop i from: 1 to: 60 {
            player opp <- opps[i mod 3];
            create game(p1: a, p2: opp, pair_key: "g" + i) number: 1;
            if a.pending_action[opp] != last(a.my_moves_per_other[opp]) { mismatch <- true; }
            if i mod 10 = 0 { ask world { do evolution_step(); } }
        }
        assert not mismatch;
        assert a.character = "QLEARN";
    }
}

experiment test_compat_core_disables_noncore type: test {
    test "compat_core wyłącza wszystkie mechanizmy spoza rdzenia i tworzy tylko strategie klasyczne" {
        // najpierw włącz wszystko, co nie należy do rdzenia
        nb_QLEARN <- 5; nb_AQLEARN <- 5;
        movement_sensitivity <- 2.0; env_influence_qlearn <- 0.5;
        social_sensitivity_aqlearn <- 1.5; social_learning_boost_aqlearn <- 2.0;
        broken_windows_sensitivity <- 0.4; character_strength_qlearn <- 0.6;
        unlimited_games <- false;
        assert length(world.core_violations()) = 7;

        compat_N <- 200;
        compat_mix <- "equal";
        ask world { do apply_compat_core(); }
        assert empty(world.core_violations());
        assert nb_TFT + nb_ALLC + nb_ALLD + nb_FTFT + nb_TF2T + nb_GRIM + nb_WSLS = 200;
        assert classic_start_cooperate;

        compat_mix <- "tft_alld";
        ask world { do apply_compat_core(); }
        assert nb_ALLD = 40 and nb_TFT = 160;
        assert nb_ALLC + nb_FTFT + nb_TF2T + nb_GRIM + nb_WSLS = 0;
    }
}

experiment test_payoff_presets type: test {
    test "presety macierzy wypłat przechodzą walidację swojego typu gry" {
        loop pr over: ["PD_classic", "weak_PD", "snowdrift"] {
            payoff_preset <- pr;
            ask world { do apply_payoff_preset(); }
            assert world.payoffs_valid();
        }
    }
}

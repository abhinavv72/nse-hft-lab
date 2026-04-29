#pragma once

#include <string>
#include <vector>

#include "order.hpp"

namespace nse::engine {

struct Trade {
  std::string trade_id;
  std::string symbol;
  double price{0.0};
  int qty{0};
  std::string taker_order_id;
  std::string maker_order_id;
  std::string aggressor_side;
  std::string timestamp;
};

struct DepthLevel {
  double price{0.0};
  int qty{0};
};

struct Snapshot {
  std::string symbol;
  std::vector<DepthLevel> bids;
  std::vector<DepthLevel> asks;
  double best_bid{0.0};
  bool has_best_bid{false};
  double best_ask{0.0};
  bool has_best_ask{false};
  std::string timestamp;
};

struct SubmitResult {
  Order order;
  std::vector<Trade> trades;
  Snapshot snapshot;
  std::string status;
};

}  // namespace nse::engine

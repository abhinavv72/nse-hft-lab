#pragma once

#include <string>

namespace nse::engine {

struct Order {
  std::string order_id;
  std::string symbol;
  std::string side;
  std::string order_type;
  double price{0.0};
  int qty{0};
  int remaining_qty{0};
  std::string timestamp;
  std::string owner{"manual"};
  std::string strategy_id;
};

}  // namespace nse::engine

import type { OrderRecord, TradeRecord } from "../types";

interface BlotterProps {
  orders: OrderRecord[];
  fills: TradeRecord[];
}

export default function Blotter({ orders, fills }: BlotterProps) {
  return (
    <div>
      <div className="panel-header">
        <h2>Orders & Fills</h2>
        <span>{orders.length} orders / {fills.length} fills</span>
      </div>
      <div className="blotter-grid">
        <div>
          <h3>Orders</h3>
          <div className="table-grid compact">
            <div className="row head">
              <span>Status</span>
              <span>Symbol</span>
              <span>Side</span>
              <span>Px</span>
              <span>Qty</span>
            </div>
            {orders.slice(0, 12).map((order) => (
              <div className="row" key={order.order_id}>
                <span>{order.status}</span>
                <span>{order.symbol}</span>
                <span className={order.side === "BUY" ? "buy-text" : "sell-text"}>{order.side}</span>
                <span>{order.price.toFixed(2)}</span>
                <span>{order.filled_qty}/{order.qty}</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <h3>Fills</h3>
          <div className="table-grid compact">
            <div className="row head">
              <span>Trade</span>
              <span>Symbol</span>
              <span>Side</span>
              <span>Px</span>
              <span>Qty</span>
            </div>
            {fills.slice(0, 12).map((fill) => (
              <div className="row" key={fill.trade_id}>
                <span>{fill.trade_id}</span>
                <span>{fill.symbol}</span>
                <span className={fill.aggressor_side === "BUY" ? "buy-text" : "sell-text"}>{fill.aggressor_side}</span>
                <span>{fill.price.toFixed(2)}</span>
                <span>{fill.qty}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

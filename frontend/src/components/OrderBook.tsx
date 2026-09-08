import type { BookSnapshot } from "../types";

interface OrderBookProps {
  symbol: string;
  book?: BookSnapshot;
}

export default function OrderBook({ symbol, book }: OrderBookProps) {
  return (
    <div>
      <div className="panel-header">
        <h2>Order Book</h2>
        <span>{symbol}</span>
      </div>
      <div className="book-grid">
        <div>
          <h3>Bids</h3>
          {(book?.bids ?? []).map((level) => (
            <div className="book-row buy" key={`bid-${level.price}`}>
              <span>{level.price.toFixed(2)}</span>
              <span>{level.qty}</span>
            </div>
          ))}
        </div>
        <div>
          <h3>Asks</h3>
          {(book?.asks ?? []).map((level) => (
            <div className="book-row sell" key={`ask-${level.price}`}>
              <span>{level.price.toFixed(2)}</span>
              <span>{level.qty}</span>
            </div>
          ))}
        </div>
      </div>
      {!book && <p className="empty-state">Choose a stock after starting the simulator to view its bid and ask levels.</p>}
    </div>
  );
}

import type { IPrimitivePaneRenderer, IPrimitivePaneView, ISeriesPrimitive, SeriesAttachedParameter, Time, UTCTimestamp } from "lightweight-charts";
import type { CanvasRenderingTarget2D } from "fancy-canvas";

export interface TradeAnnotation {
  id: string;
  time: UTCTimestamp;
  price: number;
  anchor: "above" | "below";
  color: string;
  lines: string[];
}

interface PositionedAnnotation extends TradeAnnotation { x: number; y: number; }

class TradeAnnotationRenderer implements IPrimitivePaneRenderer {
  private annotations: PositionedAnnotation[] = [];

  update(annotations: PositionedAnnotation[]) { this.annotations = annotations; }

  draw(target: CanvasRenderingTarget2D): void {
    target.useMediaCoordinateSpace(({ context, mediaSize }) => {
      context.save();
      context.beginPath();
      context.rect(0, 0, mediaSize.width, mediaSize.height);
      context.clip();
      context.font = "12px sans-serif";
      context.textBaseline = "middle";
      const occupied: { left: number; right: number; top: number; bottom: number; anchor: "above" | "below" }[] = [];
      for (const item of [...this.annotations].sort((left, right) => left.x - right.x || left.id.localeCompare(right.id))) {
        const width = Math.max(...item.lines.map((line) => context.measureText(line).width)) + 16;
        const height = item.lines.length * 16 + 10;
        let top = item.anchor === "above" ? item.y - height - 18 : item.y + 18;
        const left = Math.max(2, Math.min(mediaSize.width - width - 2, item.x - width / 2));
        const overlaps = (candidate: number) => occupied.some((box) => box.anchor === item.anchor && left < box.right && left + width > box.left && candidate < box.bottom && candidate + height > box.top);
        while (overlaps(top)) top += item.anchor === "above" ? -(height + 6) : height + 6;
        const cardY = Math.max(2, Math.min(mediaSize.height - height - 2, top));
        const leaderY = item.anchor === "above" ? cardY + height : cardY;
        context.strokeStyle = item.color;
        context.lineWidth = 1;
        context.beginPath();
        context.moveTo(item.x, item.y);
        context.lineTo(item.x, leaderY);
        context.stroke();
        context.fillStyle = "rgba(15, 23, 42, 0.78)";
        context.beginPath();
        context.roundRect(left, cardY, width, height, 4);
        context.fill();
        context.strokeStyle = item.color;
        context.stroke();
        context.fillStyle = "#f8fafc";
        item.lines.forEach((line, index) => context.fillText(line, left + 8, cardY + 13 + index * 16));
        occupied.push({ left, right: left + width, top: cardY, bottom: cardY + height, anchor: item.anchor });
      }
      context.restore();
    });
  }
}

class TradeAnnotationPaneView implements IPrimitivePaneView {
  private readonly rendererValue = new TradeAnnotationRenderer();
  private annotations: TradeAnnotation[] = [];
  private parameters: SeriesAttachedParameter<Time> | null = null;

  attached(parameters: SeriesAttachedParameter<Time>) { this.parameters = parameters; }
  update(annotations: TradeAnnotation[]) { this.annotations = annotations; }
  updateAllViews() {
    if (!this.parameters) return;
    const { chart, series } = this.parameters;
    this.rendererValue.update(this.annotations.flatMap((annotation) => {
      const x = chart.timeScale().timeToCoordinate(annotation.time);
      const y = series.priceToCoordinate(annotation.price);
      return x === null || y === null ? [] : [{ ...annotation, x, y }];
    }));
  }
  renderer(): IPrimitivePaneRenderer { return this.rendererValue; }
}

export class TradeAnnotationPrimitive implements ISeriesPrimitive<Time> {
  private readonly paneView = new TradeAnnotationPaneView();
  private requestUpdate: (() => void) | null = null;

  attached(parameters: SeriesAttachedParameter<Time>) { this.requestUpdate = parameters.requestUpdate; this.paneView.attached(parameters); }
  detached() { this.requestUpdate = null; }
  updateAllViews() { this.paneView.updateAllViews(); }
  paneViews(): readonly IPrimitivePaneView[] { return [this.paneView]; }
  setAnnotations(annotations: TradeAnnotation[]) { this.paneView.update(annotations); this.requestUpdate?.(); }
}

export function formatTradeVolume(value: number, unit: string): string {
  return `${value.toFixed(2)} ${unit}`;
}

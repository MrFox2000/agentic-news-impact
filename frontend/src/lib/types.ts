export type Step = {
  node: string;
  detail: string;
};

export type StreamEvent =
  | { type: "step"; node: string; detail: string }
  | { type: "report"; markdown: string }
  | { type: "error"; message: string }
  | { type: "done" };

export type RunHandlers = {
  onStep: (step: Step) => void;
  onReport: (markdown: string) => void;
  onError: (message: string) => void;
};

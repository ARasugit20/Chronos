import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { resolveWebSocketBaseUrl } from "../api/config";
import type { Signal } from "../types/domain";

const WS_URL = `${resolveWebSocketBaseUrl()}/ws/signals`;

export type ConnectionStatus = "connected" | "reconnecting" | "disconnected";

export function useSignalWebSocket() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [delay, setDelay] = useState(1000);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let timer: ReturnType<typeof setTimeout>;

    const connect = () => {
      setStatus("reconnecting");
      ws = new WebSocket(WS_URL);
      ws.onopen = () => {
        setStatus("connected");
        setDelay(1000);
      };
      ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type === "snapshot") {
          queryClient.setQueryData(["signals", false], payload.data as Signal[]);
        }
        if (payload.type === "signal") {
          queryClient.setQueryData(["signals", false], (old: Signal[] | undefined) => {
            const prev = old ?? [];
            return [payload.data as Signal, ...prev].slice(0, 50);
          });
        }
      };
      ws.onclose = () => {
        setStatus("disconnected");
        timer = setTimeout(() => {
          setDelay((d) => Math.min(d * 2, 30_000));
          connect();
        }, delay);
      };
    };

    connect();
    return () => {
      ws?.close();
      clearTimeout(timer);
    };
  }, [queryClient, delay]);

  return { connectionStatus: status };
}

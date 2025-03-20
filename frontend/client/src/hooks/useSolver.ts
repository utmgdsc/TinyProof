// Claude 3.5 Sonnet was used to help write this code.
import { useState, useEffect } from "react";

interface SolverProps {
  // The URL of the solver websocket
  url: string;

  // Runs when the websocket is connected
  onConnect?: () => void;

  // Runs when the websocket is disconnected
  onDisconnect?: () => void;

  // Runs when an error occurs
  onError?: (event: Event) => void;

  // Runs when a proof step is received
  onProofStep?: (proof: string) => void;
}

export default function useSolver({
  url,
  onConnect,
  onDisconnect,
  onError,
  onProofStep,
}: SolverProps) {
  const [proofSteps, setProofSteps] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [finalProof, setFinalProof] = useState<string | null>(null);

  useEffect(() => {
    // Create WebSocket connection
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setIsConnected(true);
      console.log("Connected to solver websocket");
      onConnect?.();
    };

    ws.onmessage = (event) => {
      const proof = event.data;

      // Add new proof variation to the list
      setProofSteps((prev) => [...prev, proof]);

      // Check if this is the final correct proof
      if (proof.includes("PROOF_COMPLETE")) {
        // You can adjust this condition
        setFinalProof(proof);
        ws.close();
      }

      onProofStep?.(proof);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log("Disconnected from solver websocket");
      onDisconnect?.();
    };

    ws.onerror = (event) => {
      console.error("WebSocket error:", event);
      onError?.(event);
    };

    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, [url, onConnect, onDisconnect, onError, onProofStep]);

  return {
    proofSteps,
    isConnected,
    finalProof,
  };
}

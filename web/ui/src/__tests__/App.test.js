

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import '@testing-library/jest-dom';
import App from "../App";

describe("Sophia Web UI základní integrace", () => {
  test("Zobrazí hlavní menu a komponenty", () => {
    render(<App />);
    expect(screen.getByText(/Sophia Web UI/i)).toBeInTheDocument();
    expect(screen.getByText(/Přihlášení/)).toBeInTheDocument();
    expect(screen.getByText(/Chat/)).toBeInTheDocument();
    expect(screen.getByText(/Nahrávání/)).toBeInTheDocument();
    expect(screen.getByText(/Soubory/)).toBeInTheDocument();
    expect(screen.getByText(/Profil/)).toBeInTheDocument();
    expect(screen.getByText(/Notifikace/)).toBeInTheDocument();
    expect(screen.getByText(/Nastavení/)).toBeInTheDocument();
    expect(screen.getByText(/Helpdesk/)).toBeInTheDocument();
    expect(screen.getByText(/Jazyk/)).toBeInTheDocument();
    expect(screen.getByText(/Role/)).toBeInTheDocument();
  });

  test("Chat komponenta umožňuje zadat a zobrazit zprávu (mock backend)", async () => {
    // Mock fetch pro chat endpoint
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ response: "Test odpověď od Sophie" })
      })
    );
    render(<App />);
    fireEvent.click(screen.getByText(/Chat/));
    const input = screen.getByPlaceholderText(/Napište zprávu/i);
    fireEvent.change(input, { target: { value: "Ahoj" } });
    fireEvent.click(screen.getByText(/Odeslat/));
    expect(screen.getByText(/Vy:/)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Test odpověď od Sophie/)).toBeInTheDocument();
    });
    global.fetch.mockRestore && global.fetch.mockRestore();
  });
});

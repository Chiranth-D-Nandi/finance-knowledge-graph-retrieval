import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const resp = await fetch("http://127.0.0.1:8000/qa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (err: any) {
    return NextResponse.json(
      { error: "Failed to connect to FastAPI backend", detail: err.message },
      { status: 502 }
    );
  }
}

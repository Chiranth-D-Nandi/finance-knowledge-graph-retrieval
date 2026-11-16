import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: { eventId: string } }
) {
  try {
    const backendUrl = `http://127.0.0.1:8000/impact/${params.eventId}`;
    const resp = await fetch(backendUrl);
    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (err: any) {
    return NextResponse.json(
      { error: "Failed to connect to FastAPI backend", detail: err.message },
      { status: 502 }
    );
  }
}

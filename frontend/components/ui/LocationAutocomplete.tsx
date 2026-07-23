"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Loader2, MapPin } from "lucide-react";
import { toast } from "sonner";

interface LocationResult {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
}

interface LocationAutocompleteProps {
  id?: string;
  value?: string;
  onChange?: (val: string) => void;
  onSelectLocation: (data: {
    placeName: string;
    latitude: string;
    longitude: string;
    timezone?: string;
  }) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function LocationAutocomplete({
  id,
  value = "",
  onChange,
  onSelectLocation,
  disabled = false,
  placeholder = "Search for a city...",
  className = "",
}: LocationAutocompleteProps) {
  const [inputValue, setInputValue] = useState(value);
  const [suggestions, setSuggestions] = useState<LocationResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchLocations = useCallback(async (query: string) => {
    if (!query || query.length < 3) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }
    setIsLoading(true);
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=5`
      );
      const data = await res.json();
      setSuggestions(data);
      setIsOpen(data.length > 0);
    } catch (e) {
      console.error("Geocoding error:", e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isOpen && inputValue === value) return;

    const timer = setTimeout(() => {
      fetchLocations(inputValue);
    }, 500);

    return () => clearTimeout(timer);
  }, [inputValue, fetchLocations, value, isOpen]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputValue(val);
    setIsOpen(true);
    if (onChange) onChange(val);
  };

  const handleSelect = async (place: LocationResult) => {
    setInputValue(place.display_name);
    if (onChange) onChange(place.display_name);
    setIsOpen(false);
    setSuggestions([]);
    
    // Show loading state while fetching timezone
    setIsLoading(true);

    const lat = parseFloat(place.lat).toFixed(4);
    const lon = parseFloat(place.lon).toFixed(4);

    let timezone = "";
    try {
      const tzRes = await fetch(`https://timeapi.io/api/TimeZone/coordinate?latitude=${lat}&longitude=${lon}`);
      const tzData = await tzRes.json();
      if (tzData && tzData.timeZone) {
        timezone = tzData.timeZone;
        toast.success(`Found location and timezone: ${timezone}`);
      } else {
        toast.success("Location found. Please select timezone manually.");
      }
    } catch {
      toast.success("Location found. Please select timezone manually.");
    } finally {
      setIsLoading(false);
    }

    onSelectLocation({
      placeName: place.display_name,
      latitude: lat,
      longitude: lon,
      timezone: timezone || undefined,
    });
  };

  return (
    <div className="relative" ref={wrapperRef}>
      <div className="relative">
        <Input
          id={id}
          value={inputValue}
          onChange={handleInputChange}
          disabled={disabled}
          placeholder={placeholder}
          className={className}
          onFocus={() => {
            if (suggestions.length > 0) setIsOpen(true);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault(); // Prevent form submission
              if (isOpen && suggestions.length > 0) {
                handleSelect(suggestions[0]); // Select first suggestion on enter
              }
            }
          }}
          autoComplete="off"
        />
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          </div>
        )}
      </div>

      {isOpen && suggestions.length > 0 && (
        <div className="absolute top-full left-0 z-50 w-full mt-1 bg-popover text-popover-foreground border rounded-md shadow-md max-h-60 overflow-y-auto">
          <ul className="py-1">
            {suggestions.map((place) => (
              <li
                key={place.place_id}
                className="px-3 py-2 text-sm hover:bg-muted cursor-pointer flex items-start gap-2"
                onClick={() => handleSelect(place)}
              >
                <MapPin className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                <span className="line-clamp-2">{place.display_name}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
